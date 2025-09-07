from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID

from .database import Base

class Document(Base):
    """
    Modelo de la tabla que guarda el estado y la información de cada documento
    en el flujo de firma.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String, index=True)
    storage_path = Column(String, nullable=False) # Ruta en MinIO
    
    # Estados: PENDING_SIGNATURE_LEVEL_1, PENDING_SIGNATURE_LEVEL_2, COMPLETED, REJECTED
    status = Column(String, default="PENDING_SIGNATURE_LEVEL_1", nullable=False)
    
    # Nivel de la jerarquía al que le corresponde firmar
    current_signer_level = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación: Un documento puede tener muchas firmas
    signatures = relationship("Signature", back_populates="document")


class Signature(Base):
    """
    Modelo de la tabla que guarda un registro de cada firma individual.
    """
    __tablename__ = "signatures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Vinculamos esta firma a un documento
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    document = relationship("Document", back_populates="signatures")

    signed_by = Column(String, nullable=False)
    signer_level = Column(Integer, nullable=False) # Nivel 1, 2, 3...
    
    signed_at = Column(DateTime(timezone=True), server_default=func.now())