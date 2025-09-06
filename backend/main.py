import os
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask # ¡Importante!
from datetime import datetime
# --- ¡ESTA ES LA CORRECCIÓN! ---
# Cambiamos las importaciones relativas por absolutas desde la carpeta 'app'
from app import database
from app.database import engine

from app.logic.pdf_signer import PDFSigner

# Le decimos a SQLAlchemy que cree las tablas cuando la aplicación arranque
database.Base.metadata.create_all(bind=engine)
# --- FIN DE LA CORRECCIÓN ---

# --- Configuración de la Aplicación FastAPI ---
app = FastAPI(
    title="Firma EC - API",
    description="API para el sistema de firma electrónica de documentos.",
    version="1.0.0"
)

# --- Función de Limpieza ---
def cleanup_temp_dir(temp_dir: str):
    """Función para eliminar un directorio temporal de forma segura."""
    try:
        shutil.rmtree(temp_dir)
        print(f"Directorio temporal {temp_dir} eliminado.")
    except Exception as e:
        print(f"Error eliminando el directorio temporal {temp_dir}: {e}")


# --- Endpoints de la API ---

@app.get("/")
def read_root():
    return {"status": "¡Servidor de Firma EC funcionando!", "timestamp": datetime.now().isoformat()}

@app.post("/api/sign")
async def sign_document(
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
    # --- CAMBIO 1: Creamos el directorio temporal manualmente ---
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
            # --- CAMBIO 2: Mejoramos el mensaje de error para el índice de página ---
            if "Page index out of range" in message:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error de paginación: El PDF no tiene una página con índice {page_index}. Recuerda que la primera página es 0."
                )
            raise HTTPException(status_code=400, detail=f"Error al firmar: {message}")

        # --- CAMBIO 3: Usamos BackgroundTask para la limpieza ---
        # Le decimos a FastAPI que envíe el archivo, y DESPUÉS, ejecute la limpieza.
        cleanup_task = BackgroundTask(cleanup_temp_dir, temp_dir)
        return FileResponse(
            path=output_pdf_path,
            filename=f"signed_{pdf_file.filename}",
            media_type='application/pdf',
            background=cleanup_task
        )
    except HTTPException as http_exc:
        # Si ya es un error que nosotros creamos (como el del índice), lo relanzamos.
        # Y nos aseguramos de limpiar el directorio.
        cleanup_temp_dir(temp_dir)
        raise http_exc
    except Exception as e:
        # Si es un error inesperado, lo capturamos y limpiamos.
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado en el servidor: {str(e)}")