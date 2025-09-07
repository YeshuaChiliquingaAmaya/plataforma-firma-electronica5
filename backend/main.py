import os
import tempfile
import shutil
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from datetime import datetime
from sqlalchemy.orm import Session

# --- ¡AQUÍ ESTÁ LA CORRECIÓN! ---
# Le decimos a Python que busque dentro de la carpeta 'app'
from app import database, models
from app.database import engine
from app.logic.pdf_signer import PDFSigner

# Ahora que importamos 'models', SQLAlchemy sabe qué tabla crear
models.Base.metadata.create_all(bind=engine)
# --- FIN DE LA CORRECIÓN ---

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

@app.post("/api/sign")
async def sign_document(
    db: Session = Depends(database.get_db),
    pdf_file: UploadFile = File(..., description="Archivo PDF a firmar."),
    cert_file: UploadFile = File(..., description="Certificado digital (.p12)."),
    password: str = Form(..., description="Contraseña del certificado."),
    reason: str = Form("Documento revisado y aprobado", description="Razón de la firma."),
    location: str = Form("Ecuador", description="Ubicación de la firma."),
    page_index: int = Form(0, description="Índice de la página a firmar (empezando en 0)."),
    x_coord: float = Form(400.0, description="Coordenada X de la esquina inferior izquierda."),
    y_coord: float = Form(100.0, description="Coordenada Y de la esquina inferior izquierda."),
    width: float = Form(150.0, description="Ancho del sello de la firma.")
):
    temp_dir = tempfile.mkdtemp()
    try:
        input_pdf_path = os.path.join(temp_dir, pdf_file.filename)
        cert_path = os.path.join(temp_dir, cert_file.filename)
        output_pdf_path = os.path.join(temp_dir, f"signed_{pdf_file.filename}")

        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        with open(cert_path, "wb") as buffer:
            shutil.copyfileobj(cert_file.file, buffer)

        signer = PDFSigner(cert_path=cert_path, password=password)
        
        success, message = await signer.async_sign_file(
            input_pdf=input_pdf_path,
            output_pdf=output_pdf_path,
            reason=reason,
            location=location,
            page_index=page_index,
            x_coord=x_coord,
            y_coord=y_coord,
            width=width
        )
        
        if not success:
            if "Page index out of range" in message:
                raise HTTPException(status_code=400, detail=f"Error de paginación: El PDF no tiene una página con índice {page_index}.")
            raise HTTPException(status_code=400, detail=f"Error al firmar: {message}")

        new_record = models.SignatureRecord(
            original_pdf_filename=pdf_file.filename,
            certificate_filename=cert_file.filename,
            signature_reason=reason,
            signature_location=location,
            signed_by=signer.cert_subject
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        print(f"Registro de firma guardado con ID: {new_record.id}")

        cleanup_task = BackgroundTask(cleanup_temp_dir, temp_dir)
        return FileResponse(
            path=output_pdf_path,
            filename=f"signed_{pdf_file.filename}",
            media_type='application/pdf',
            background=cleanup_task
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        if 'db' in locals() and db.is_active:
            db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado en el servidor: {str(e)}")