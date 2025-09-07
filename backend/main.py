from fastapi import FastAPI
from app import database, models
from app.database import engine
from app.routers import documents # ¡Importamos nuestro nuevo router!

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Firma EC - API",
    description="API para el sistema de firma electrónica de documentos.",
    version="1.0.0"
)

# Incluimos las rutas de documentos en la aplicación principal
app.include_router(documents.router)

@app.get("/")
def read_root():
    return {"status": "¡Servidor de Firma EC funcionando!"}