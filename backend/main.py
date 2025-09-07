import os
import tempfile
import shutil
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
from uuid import UUID

# Importaciones de nuestro proyecto
from app import database, models, schemas, minio_client
from app.database import engine
from app.logic.pdf_signer import PDFSigner

models.Base.metadata.create_all(bind=engine)

# Nombre del bucket que usaremos en MinIO
DOCUMENTS_BUCKET = "documents"

app = FastAPI(
    title="Firma EC - API",
    description="API para el sistema de firma electrónica de documentos.",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    # Al arrancar la API, nos aseguramos de que el bucket exista
    minio_client.create_bucket_if_not_exists(DOCUMENTS_BUCKET)

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
    temp_dir = tempfile.mkdtemp()
    try:
        # Guardamos el archivo subido en una ruta temporal
        input_pdf_path = os.path.join(temp_dir, pdf_file.filename)
        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)

        # --- CAMBIO 2: Usamos el módulo 'uuid' correctamente ---
        doc_id = uuid.uuid4()
        storage_path = str(doc_id)

        minio_client.upload_file(
            bucket_name=DOCUMENTS_BUCKET,
            file_path=input_pdf_path,
            object_name=storage_path
        )
        
        new_document = models.Document(
            id=doc_id,
            original_filename=pdf_file.filename,
            storage_path=storage_path,
            status="PENDIENTE_FIRMA_NIVEL_1",
            current_signer_level=1
        )
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
        
        print(f"Documento '{pdf_file.filename}' registrado y subido a MinIO con ID: {new_document.id}.")
        
        return new_document
    finally:
        cleanup_temp_dir(temp_dir)

@app.post("/api/documents/{document_id}/sign")
async def sign_existing_document(
    document_id: UUID,
    db: Session = Depends(database.get_db),
    # ¡YA NO PEDIMOS EL PDF!
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
        raise HTTPException(status_code=403, detail=f"No es el turno de este firmante. Se espera el nivel {doc_record.current_signer_level}.")

    temp_dir = tempfile.mkdtemp()
    try:
        # Descargamos el archivo actual desde MinIO a una ruta temporal
        input_pdf_path = os.path.join(temp_dir, "current_version.pdf")
        minio_client.download_file(
            bucket_name=DOCUMENTS_BUCKET,
            object_name=doc_record.storage_path,
            file_path=input_pdf_path
        )

        cert_path = os.path.join(temp_dir, cert_file.filename)
        output_pdf_path = os.path.join(temp_dir, "signed_version.pdf")

        with open(cert_path, "wb") as buffer:
            shutil.copyfileobj(cert_file.file, buffer)
            
        signer = PDFSigner(cert_path=cert_path, password=password)
        
        success, message = await signer.async_sign_file(
            input_pdf=input_pdf_path,
            output_pdf=output_pdf_path,
            reason=reason, location=location,
            page_index=0, x_coord=100 + (signer_level * 20), y_coord=100, width=150
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Error técnico al firmar: {message}")

        # Subimos la nueva versión firmada a MinIO, sobrescribiendo la anterior
        minio_client.upload_file(
            bucket_name=DOCUMENTS_BUCKET,
            file_path=output_pdf_path,
            object_name=doc_record.storage_path
        )
            
        new_signature = models.Signature(document_id=doc_record.id, signed_by=signer.cert_subject, signer_level=signer_level)
        db.add(new_signature)
        
        doc_record.current_signer_level += 1
        doc_record.status = f"PENDIENTE_FIRMA_NIVEL_{doc_record.current_signer_level}"
        
        db.commit()
        
        print(f"Firma de nivel {signer_level} añadida. El documento ahora espera al nivel {doc_record.current_signer_level}.")

        cleanup_task = BackgroundTask(cleanup_temp_dir, temp_dir)
        return FileResponse(
            path=output_pdf_path,
            filename=f"firmado_nivel_{signer_level}_{doc_record.original_filename}",
            media_type='application/pdf',
            background=cleanup_task
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error inesperado en el servidor: {str(e)}")