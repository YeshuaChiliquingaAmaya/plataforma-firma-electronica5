from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Esquema para una firma individual (para mostrar en las respuestas)
class SignatureBase(BaseModel):
    id: UUID
    signed_by: str
    signer_level: int
    signed_at: datetime

    class Config:
        orm_mode = True # Permite que el modelo se cree a partir de un objeto de la base de datos

# Esquema para un documento (para mostrar en las respuestas)
class DocumentBase(BaseModel):
    id: UUID
    original_filename: str
    status: str
    current_signer_level: int
    created_at: datetime
    signatures: List[SignatureBase] = []

    class Config:
        orm_mode = True