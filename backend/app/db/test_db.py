"""
Test de conexión a PostgreSQL con validaciones completas
"""
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.db.database import engine, DATABASE_URL
import sys


def test_basic_connection():
    """Test básico de conexión"""
    print("1️⃣  Test básico de conexión...")
    try:
        conn = engine.connect()
        print("   ✓ Conexión exitosa")
        conn.close()
        return True
    except OperationalError as e:
        print(f"   ✗ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error inesperado: {e}")
        return False


def test_query_execution():
    """Test de ejecución de queries"""
    print("\n2️⃣  Test de ejecución de queries...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row[0] == 1:
                print("   ✓ Query ejecutada correctamente")
                return True
            else:
                print("   ✗ Resultado inesperado")
                return False
    except Exception as e:
        print(f"   ✗ Error ejecutando query: {e}")
        return False


def test_database_info():
    """Test de información de la DB"""
    print("\n3️⃣  Información de la base de datos...")
    try:
        with engine.connect() as conn:
            # Versión
            version = conn.execute(text("SELECT version()")).fetchone()[0]
            print(f"   PostgreSQL: {version.split(',')[0]}")
            
            # Usuario actual
            user = conn.execute(text("SELECT current_user")).fetchone()[0]
            print(f"   Usuario: {user}")
            
            # Base de datos actual
            db = conn.execute(text("SELECT current_database()")).fetchone()[0]
            print(f"   Database: {db}")
            
            return True
    except Exception as e:
        print(f"   ✗ Error obteniendo info: {e}")
        return False


def test_table_operations():
    """Test de operaciones con tablas"""
    print("\n4️⃣  Test de operaciones con tablas...")
    try:
        with engine.connect() as conn:
            # Intentar crear una tabla de prueba
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id SERIAL PRIMARY KEY,
                    test_value VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("   ✓ Tabla de prueba creada")
            
            # Insertar un registro
            conn.execute(text("""
                INSERT INTO test_connection (test_value) 
                VALUES ('Connection test successful')
            """))
            conn.commit()
            print("   ✓ Registro insertado")
            
            # Leer el registro
            result = conn.execute(text("""
                SELECT test_value FROM test_connection 
                ORDER BY id DESC LIMIT 1
            """))
            row = result.fetchone()
            print(f"   ✓ Registro leído: '{row[0]}'")
            
            # Limpiar
            conn.execute(text("DROP TABLE test_connection"))
            conn.commit()
            print("   ✓ Tabla de prueba eliminada")
            
            return True
    except Exception as e:
        print(f"   ✗ Error en operaciones: {e}")
        return False


def run_all_tests():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("🧪 PRUEBAS DE CONEXIÓN A POSTGRESQL")
    print("=" * 60)
    print(f"\n📍 URL de conexión: {DATABASE_URL.split('@')[1]}")  # Sin mostrar credenciales
    print()
    
    tests = [
        test_basic_connection,
        test_query_execution,
        test_database_info,
        test_table_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed}/{total} tests pasados")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ ¡Todos los tests pasaron! La base de datos está correctamente configurada.\n")
        return 0
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa la configuración.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())