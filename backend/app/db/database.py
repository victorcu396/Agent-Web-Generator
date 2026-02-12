import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Obtener DATABASE_URL desde .env o usar valor por defecto
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/postgres"
)

# Crear engine con configuración de pool
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica la conexión antes de usar
    pool_size=5,
    max_overflow=10,
    echo=False  # Cambiar a True para debug SQL
)

def test_connection():
    """
    Prueba la conexión a la base de datos.
    Retorna True si conecta, False si falla.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Conexión a PostgreSQL exitosa")
            print(f"  Database: {engine.url.database}")
            print(f"  Host: {engine.url.host}:{engine.url.port}")
            return True
    except OperationalError as e:
        print("✗ Error de conexión a PostgreSQL:")
        print(f"  {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {str(e)}")
        return False

def get_db_info():
    """
    Obtiene información sobre la base de datos.
    """    
    
    try:
        with engine.connect() as conn:
            # Versión de PostgreSQL
            version = conn.execute(text("SELECT version()")).fetchone()[0]
            
            # Número de tablas
            tables_count = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchone()[0]
            
            print("\n📊 Información de la base de datos:")
            print(f"  PostgreSQL: {version.split(',')[0]}")
            print(f"  Tablas en schema 'public': {tables_count}")
            
            # Listar tablas si existen
            if tables_count > 0:
                tables = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)).fetchall()
                print("\n  Tablas disponibles:")
                for table in tables:
                    print(f"    - {table[0]}")
            
    except Exception as e:
        print(f"Error obteniendo información: {str(e)}")    

if __name__ == "__main__":
    print("🔍 Verificando conexión a PostgreSQL...\n")
    if test_connection():
        get_db_info()
    else:
        print("\n⚠️  Asegúrate de que PostgreSQL está corriendo")
        print("   y que las credenciales en .env son correctas")
