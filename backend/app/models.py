from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID

from .database import Base

class SignatureRecord(Base):
    """
    Este es el modelo de la tabla que guardará un registro de cada firma.
    SQLAlchemy lo traducirá a una tabla SQL en PostgreSQL.
    """
    __tablename__ = "signature_records"

    # Columnas de la tabla
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nombres de los archivos originales
    original_pdf_filename = Column(String, index=True)
    certificate_filename = Column(String)

    # Datos proporcionados por el usuario
    signature_reason = Column(String)
    signature_location = Column(String)
    signed_by = Column(String) # Guardaremos el 'common_name' del certificado

    # Timestamps automáticos
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Puedes añadir más campos después si lo necesitas
    # status = Column(String, default="SUCCESS")