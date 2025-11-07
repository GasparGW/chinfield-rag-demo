#!/usr/bin/env python3
"""
Script de Testing Local - Chinfield RAG Demo
Valida que todo funcione antes de deployment a Railway
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Imprimir encabezado"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(step_num, total, text):
    """Imprimir paso"""
    print(f"[{step_num}/{total}] {text}...")

def check_file_exists(filepath, description):
    """Verificar que un archivo existe"""
    if Path(filepath).exists():
        print(f"  ✅ {description}: {filepath}")
        return True
    else:
        print(f"  ❌ {description} NO ENCONTRADO: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Verificar que un directorio existe"""
    if Path(dirpath).exists() and Path(dirpath).is_dir():
        print(f"  ✅ {description}: {dirpath}")
        return True
    else:
        print(f"  ❌ {description} NO ENCONTRADO: {dirpath}")
        return False

def test_imports():
    """Test 1: Verificar que todas las dependencias se pueden importar"""
    print_step(1, 7, "Verificando imports de Python")
    
    required_modules = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('openai', 'OpenAI'),
        ('chromadb', 'ChromaDB'),
        ('sentence_transformers', 'Sentence Transformers'),
    ]
    
    all_ok = True
    for module, name in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} NO INSTALADO")
            all_ok = False
    
    return all_ok

def test_file_structure():
    """Test 2: Verificar estructura de archivos"""
    print_step(2, 7, "Verificando estructura de archivos")
    
    required_files = [
        ('app.py', 'API principal'),
        ('rag_system_api.py', 'Sistema RAG'),
        ('build_chromadb.py', 'Script de build'),
        ('requirements.txt', 'Dependencias'),
        ('nixpacks.toml', 'Configuración Railway'),
        ('Procfile', 'Procfile'),
        ('runtime.txt', 'Runtime Python'),
        ('config/settings.py', 'Configuración'),
    ]
    
    all_ok = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_ok = False
    
    return all_ok

def test_data_directory():
    """Test 3: Verificar que existen los archivos de datos"""
    print_step(3, 7, "Verificando archivos de productos")
    
    if not check_directory_exists('data/products', 'Directorio de productos'):
        return False
    
    # Contar archivos .txt
    product_files = list(Path('data/products').glob('*.txt'))
    print(f"  ℹ️  Encontrados {len(product_files)} archivos de productos")
    
    if len(product_files) < 10:
        print(f"  ⚠️  Se esperaban al menos 10 archivos, encontrados {len(product_files)}")
        return False
    
    print(f"  ✅ {len(product_files)} productos listos para indexar")
    return True

def test_chromadb_build():
    """Test 4: Ejecutar build de ChromaDB"""
    print_step(4, 7, "Construyendo ChromaDB")
    
    print("  ⏳ Ejecutando build_chromadb.py...")
    result = os.system('python3 build_chromadb.py')
    
    if result == 0:
        print("  ✅ ChromaDB construida exitosamente")
        return True
    else:
        print("  ❌ Error en construcción de ChromaDB")
        return False

def test_chromadb_exists():
    """Test 5: Verificar que ChromaDB se creó correctamente"""
    print_step(5, 7, "Verificando ChromaDB")
    
    chroma_path = Path('models/chroma_db')
    
    if not chroma_path.exists():
        print(f"  ❌ Directorio ChromaDB no existe")
        return False
    
    # Verificar que hay archivos dentro
    chroma_files = list(chroma_path.glob('*'))
    if len(chroma_files) == 0:
        print(f"  ❌ ChromaDB vacía")
        return False
    
    print(f"  ✅ ChromaDB creada con {len(chroma_files)} archivos")
    
    # Verificar build_info.json
    build_info = chroma_path / 'build_info.json'
    if build_info.exists():
        import json
        with open(build_info) as f:
            info = json.load(f)
        print(f"  ℹ️  Documentos indexados: {info.get('total_documents', 0)}")
        print(f"  ℹ️  Modelo embeddings: {info.get('embedding_model', 'unknown')}")
    
    return True

def test_env_variables():
    """Test 6: Verificar variables de entorno"""
    print_step(6, 7, "Verificando variables de entorno")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key:
        print("  ⚠️  OPENAI_API_KEY no configurada")
        print("  ℹ️  Configurá: export OPENAI_API_KEY='tu-api-key'")
        return False
    
    print(f"  ✅ OPENAI_API_KEY configurada ({openai_key[:8]}...)")
    return True

def test_api_startup():
    """Test 7: Verificar que la API puede arrancar"""
    print_step(7, 7, "Testing arranque de API")
    
    try:
        # Importar app sin ejecutarla
        sys.path.insert(0, '.')
        from app import app, get_rag, config
        
        print(f"  ✅ FastAPI app importada correctamente")
        print(f"  ℹ️  Configuración cargada: {config.collection_name}")
        
        # Intentar inicializar RAG (sin hacer queries)
        try:
            rag = get_rag()
            print(f"  ✅ RAG System inicializado")
            return True
        except Exception as e:
            print(f"  ❌ Error inicializando RAG: {e}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error importando app: {e}")
        return False

def main():
    """Función principal de testing"""
    print_header("🧪 TESTING LOCAL - CHINFIELD RAG DEMO")
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"📂 Directorio de trabajo: {os.getcwd()}\n")
    
    # Ejecutar tests
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Estructura", test_file_structure()))
    results.append(("Datos", test_data_directory()))
    results.append(("Build ChromaDB", test_chromadb_build()))
    results.append(("Verificar ChromaDB", test_chromadb_exists()))
    results.append(("Variables ENV", test_env_variables()))
    results.append(("API Startup", test_api_startup()))
    
    # Resumen
    print_header("📊 RESUMEN DE TESTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print(f"\n  Total: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n" + "="*70)
        print("  🎉 ¡TODOS LOS TESTS PASARON!")
        print("  ✅ El sistema está listo para deployment a Railway")
        print("="*70 + "\n")
        return 0
    else:
        print("\n" + "="*70)
        print("  ⚠️  ALGUNOS TESTS FALLARON")
        print("  ❌ Resolver los errores antes de hacer deploy")
        print("="*70 + "\n")
        return 1

if __name__ == "__main__":
    exit(main())
