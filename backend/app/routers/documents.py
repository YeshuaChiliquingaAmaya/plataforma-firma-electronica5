import os
import tempfile
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

# Importamos desde las carpetas correctas usando la estructura de paquetes
from .. import database, models, schemas, minio_client
from ..logic.pdf_signer import PDFSigner

# Creamos un router. Es como una mini-aplicación de FastAPI.
router = APIRouter(
    prefix="/api/documents", # Todas las rutas en este archivo empezarán con /api/documents
    tags=["documents"],      # Agrupa estas rutas en la documentación de la API
)

DOCUMENTS_BUCKET = "documents"

def cleanup_temp_dir(temp_dir: str):
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error limpiando el directorio temporal {temp_dir}: {e}")

# --- ENDPOINT 1: SUBIR Y REGISTRAR UN NUEVO DOCUMENTO ---
@router.post("/", response_model=schemas.DocumentBase)
async def upload_document(
    db: Session = Depends(database.get_db),
    pdf_file: UploadFile = File(..., description="PDF inicial a firmar.")
):
    temp_dir = tempfile.mkdtemp()
    try:
        input_pdf_path = os.path.join(temp_dir, pdf_file.filename)
        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)

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
        
        print(f"Documento '{pdf_file.filename}' registrado con ID: {new_document.id}.")
        return new_document
    finally:
        cleanup_temp_dir(temp_dir)

# --- ENDPOINT 2: FIRMAR UN DOCUMENTO EXISTENTE ---
@router.post("/{document_id}/sign")
async def sign_existing_document(
    document_id: UUID,
    db: Session = Depends(database.get_db),
    cert_file: UploadFile = File(..., description="Certificado digital (.p12)."),
    password: str = Form(..., description="Contraseña del certificado."),
    signer_level: int = Form(..., description="Nivel jerárquico del firmante."),
    reason: str = Form("Documento revisado y aprobado", description="Razón de la firma."),
    location: str = Form("Ecuador", description="Ubicación de la firma."),
    page_index: int = Form(...),
    x_coord: float = Form(...),
    y_coord: float = Form(...),
    width: float = Form(...)  # <--- ¡AQUÍ ESTÁ LA CORRECCIÓN!
): # <--- Se añade el paréntesis de cierre aquí
    
    doc_record = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc_record:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
        
    if doc_record.current_signer_level != signer_level:
        raise HTTPException(status_code=403, detail=f"No es el turno de este firmante. Se espera el nivel {doc_record.current_signer_level}.")

    temp_dir = tempfile.mkdtemp()
    try:
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
        
        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
        # Eliminamos el cálculo dinámico y usamos directamente los parámetros
        # que nos llegan desde el frontend.
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
            raise HTTPException(status_code=400, detail=f"Error técnico al firmar: {message}")

        minio_client.upload_file(
            bucket_name=DOCUMENTS_BUCKET,
            file_path=output_pdf_path,
            object_name=doc_record.storage_path
        )
            
        new_signature = models.Signature(document_id=doc_record.id, signed_by=signer.cert_subject, signer_level=signer_level)
        db.add(new_signature)
        
        doc_record.current_signer_level += 1
        doc_record.status = f"PENDIENTE_FIRMA_NIVEL_{doc_record.current_signer_level}"
        # TODO: Lógica para cambiar a "COMPLETADO" si era el último firmante
        
        db.commit()
        
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

# --- ENDPOINT NUEVO: DESCARGAR UN DOCUMENTO PARA PREVISUALIZACIÓN ---
@router.get("/{document_id}/download")
async def download_document_for_preview(
    document_id: UUID,
    db: Session = Depends(database.get_db)
):
    """
    Descarga el archivo PDF actual de un documento desde MinIO para
    que el frontend pueda previsualizarlo.
    """
    # 1. Buscamos el registro del documento en la base de datos
    doc_record = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc_record:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    # 2. Creamos un directorio temporal para la descarga
    temp_dir = tempfile.mkdtemp()
    local_pdf_path = os.path.join(temp_dir, doc_record.original_filename)

    try:
        # 3. Usamos nuestro cliente de MinIO para descargar el archivo
        minio_client.download_file(
            bucket_name=DOCUMENTS_BUCKET,
            object_name=doc_record.storage_path,
            file_path=local_pdf_path
        )
        
        # 4. Devolvemos el archivo usando FileResponse, con una tarea de limpieza
        cleanup_task = BackgroundTask(cleanup_temp_dir, temp_dir)
        return FileResponse(
            path=local_pdf_path,
            filename=doc_record.original_filename,
            media_type='application/pdf',
            background=cleanup_task
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"No se pudo obtener el archivo desde el almacenamiento: {e}")


# --- ENDPOINT 3: OBTENER DOCUMENTOS PENDIENTES (BANDEJA DE ENTRADA) ---
@router.get("/pending", response_model=List[schemas.DocumentBase])
async def get_pending_documents(
    # Podemos añadir filtros, por ejemplo, para ver los pendientes de un nivel específico
    # signer_level: Optional[int] = None, 
    db: Session = Depends(database.get_db)
):
    """
    Obtiene una lista de todos los documentos que no están en estado 'COMPLETADO'.
    Esta será la base para la bandeja de entrada de cada usuario.
    """
    # TODO: Cuando tengamos usuarios, aquí filtraremos por el usuario actual.
    query = db.query(models.Document).filter(models.Document.status != "COMPLETADO")
    
    # if signer_level:
    #     query = query.filter(models.Document.current_signer_level == signer_level)
        
    pending_docs = query.order_by(models.Document.created_at.desc()).all()
    return pending_docs