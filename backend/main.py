import os
import tempfile
import shutil
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from app import database, models, schemas
from app.database import engine
from app.logic.pdf_signer import PDFSigner

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Firma EC - API",
    description="API para el sistema de firma electrónica de documentos.",
    version="1.0.0"
)

def cleanup_temp_dir(temp_dir: str):
    try:
        shutil.rmtree(temp_dir)
        print(f"Directorio temporal {temp_dir} eliminado.")
    except Exception as e:
        print(f"Error eliminando el directorio temporal {temp_dir}: {e}")

@app.get("/")
def read_root():
    return {"status": "¡Servidor de Firma EC funcionando!", "timestamp": datetime.now().isoformat()}

@app.post("/api/documents", response_model=schemas.DocumentBase)
async def upload_document(
    db: Session = Depends(database.get_db),
    pdf_file: UploadFile = File(..., description="PDF inicial a firmar.")
):
    storage_path = f"minio_path/{pdf_file.filename}"
    new_document = models.Document(
        original_filename=pdf_file.filename,
        storage_path=storage_path,
        status="PENDIENTE_FIRMA_NIVEL_1",
        current_signer_level=1
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    print(f"Documento '{pdf_file.filename}' registrado con ID: {new_document.id} y estado inicial.")
    return new_document

@app.post("/api/documents/{document_id}/sign")
async def sign_existing_document(
    document_id: UUID,
    db: Session = Depends(database.get_db),
    # --- ¡CAMBIO AQUÍ! AÑADIMOS EL PDF ORIGINAL ---
    pdf_file: UploadFile = File(..., description="El mismo PDF original que se subió al registrar."),
    cert_file: UploadFile = File(..., description="Certificado digital (.p12)."),
    password: str = Form(..., description="Contraseña del certificado."),
    signer_level: int = Form(..., description="Nivel jerárquico del firmante."),
    reason: str = Form("Documento revisado y aprobado", description="Razón de la firma."),
    location: str = Form("Ecuador", description="Ubicación de la firma.")
):
    doc_record = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc_record:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
        
    if doc_record.current_signer_level != signer_level:
        raise HTTPException(
            status_code=403, 
            detail=f"No es el turno de este firmante. Se espera el nivel {doc_record.current_signer_level}."
        )

    temp_dir = tempfile.mkdtemp()
    try:
        # --- ¡CAMBIO AQUÍ! USAMOS EL PDF REAL ---
        # Ya no creamos un PDF vacío, usamos el que el usuario nos envía.
        input_pdf_path = os.path.join(temp_dir, pdf_file.filename)
        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        # --- FIN DEL CAMBIO ---

        cert_path = os.path.join(temp_dir, cert_file.filename)
        output_pdf_path = os.path.join(temp_dir, f"signed_{doc_record.original_filename}")

        with open(cert_path, "wb") as buffer:
            shutil.copyfileobj(cert_file.file, buffer)
            
        signer = PDFSigner(cert_path=cert_path, password=password)
        
        success, message = await signer.async_sign_file(
            input_pdf=input_pdf_path,
            output_pdf=output_pdf_path,
            reason=reason, location=location,
            # Usamos coordenadas fijas para la prueba
            page_index=0, x_coord=100, y_coord=100, width=150
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Error técnico al firmar: {message}")
            
        new_signature = models.Signature(
            document_id=doc_record.id,
            signed_by=signer.cert_subject,
            signer_level=signer_level
        )
        db.add(new_signature)
        
        doc_record.current_signer_level += 1
        doc_record.status = f"PENDIENTE_FIRMA_NIVEL_{doc_record.current_signer_level}"
        
        db.commit()
        print(f"Firma de nivel {signer_level} añadida al documento {document_id}.")
        
        cleanup_task = BackgroundTask(cleanup_temp_dir, temp_dir)
        return FileResponse(
            path=output_pdf_path,
            filename=f"signed_{doc_record.original_filename}",
            media_type='application/pdf',
            background=cleanup_task
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error inesperado en el servidor: {str(e)}")