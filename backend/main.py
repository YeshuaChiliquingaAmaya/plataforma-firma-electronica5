from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # ¡Importación nueva!
from app import database, models
from app.database import engine
from app.routers import documents 
from app.minio_client import create_bucket_if_not_exists # ¡Importación nueva!

# Nombre del bucket que usaremos en MinIO
DOCUMENTS_BUCKET = "documents"

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Firma EC - API",
    description="API para el sistema de firma electrónica de documentos.",
    version="1.0.0"
)

# --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
@app.on_event("startup")
def on_startup():
    """
    Esta función se ejecuta una sola vez, cuando la API arranca.
    Nos aseguramos de que el bucket de MinIO exista.
    """

    print("Verificando la existencia del bucket de MinIO...")
    create_bucket_if_not_exists(DOCUMENTS_BUCKET)
    print("Bucket de MinIO listo.")
# --- FIN DE LA CORRECCIÓN ---

# --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
# Definimos de dónde permitiremos las peticiones.
# En producción, esto debería ser la URL de tu aplicación real.
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitimos todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permitimos todas las cabeceras
)
# --- FIN DE LA CORRECCIÓN ---


# Incluimos las rutas de documentos en la aplicación principal
app.include_router(documents.router)

@app.get("/")
def read_root():
    return {"status": "¡Servidor de Firma EC funcionando!"}