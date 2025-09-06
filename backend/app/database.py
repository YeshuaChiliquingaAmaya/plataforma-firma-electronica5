import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Leemos la URL de conexión a la base de datos desde las variables de entorno
# que definimos en docker-compose.yml
DATABASE_URL = os.environ.get("DATABASE_URL")

# Creamos el "motor" de SQLAlchemy. Este es el punto de entrada principal
# para la base de datos.
engine = create_engine(DATABASE_URL)

# Cada instancia de SessionLocal será una sesión de base de datos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Usaremos esta clase Base para crear cada uno de los modelos ORM (las tablas)
Base = declarative_base()

# Función de dependencia para obtener una sesión de la base de datos en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()