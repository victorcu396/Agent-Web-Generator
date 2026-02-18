import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Carga las variables de entorno desde .env
load_dotenv()

# Variables individuales de conexión
db_user_name = os.getenv("DATABASE_USERNAME", "postgres")
db_password = os.getenv("DATABASE_PASSWORD", "postgres")
db_host = os.getenv("DATABASE_HOSTNAME", "127.0.0.1")
db_port = os.getenv("DATABASE_PORT", "5432")
db_name = os.getenv("DATABASE_NAME", "boilerplate_db")
db_search_path = os.getenv("DATABASE_SEARCH_PATH", "public")
db_pool_size = int(os.getenv("DATABASE_POOL_SIZE", 5))
db_pool_size_overflow = int(os.getenv("DATABASE_POOL_SIZE_OVERFLOW", 10))

# Logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Construir DATABASE_URL si no está definido en .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = (
        f"postgresql+psycopg2://{db_user_name}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

# Configuración de engine con pool y search_path
connect_args = {"options": f"-c search_path={db_search_path}"}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=db_pool_size,
    max_overflow=db_pool_size_overflow,
    echo=False,
    connect_args=connect_args
)

# Session maker y Base declarativa
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Función para obtener sesión de DB en endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para probar la conexión a la base de datos
def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Conexión a PostgreSQL exitosa ✅")
            return True
    except OperationalError as e:
        logger.error(f"Error de conexión a PostgreSQL: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return False

# Ejemplo de uso: test de conexión al iniciar la app
if __name__ == "__main__":
    test_connection()
