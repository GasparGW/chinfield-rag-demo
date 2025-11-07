"""
Build Script - Indexación de Productos en ChromaDB
Se ejecuta durante el build de Railway (antes del runtime)
"""

import os
import json
from pathlib import Path
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer


class ChromaDBBuilder:
    """Constructor de base de datos vectorial para deployment"""
    
    def __init__(
        self,
        data_dir: str = "./data/products",
        chroma_path: str = "./models/chroma_db",
        collection_name: str = "chinfield_products",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.data_dir = Path(data_dir)
        self.chroma_path = Path(chroma_path)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
    def load_product_files(self) -> List[Dict]:
        """Cargar archivos de productos desde el directorio de datos"""
        print(f"📂 Cargando archivos desde: {self.data_dir}")
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Directorio no encontrado: {self.data_dir}")
        
        documentos = []
        txt_files = sorted(self.data_dir.glob("*.txt"))
        
        if not txt_files:
            raise ValueError(f"No se encontraron archivos .txt en {self.data_dir}")
        
        print(f"   Encontrados {len(txt_files)} archivos")
        
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # Extraer metadata del contenido
                metadata = self._extract_metadata(content, file_path.stem)
                
                documentos.append({
                    'text': content,
                    'metadata': metadata,
                    'filename': file_path.name
                })
                
                print(f"   ✓ {file_path.name}")
                
            except Exception as e:
                print(f"   ✗ Error en {file_path.name}: {e}")
                continue
        
        print(f"✅ {len(documentos)} documentos cargados\n")
        return documentos
    
    def _extract_metadata(self, content: str, filename: str) -> Dict:
        """Extraer metadata del contenido del documento"""
        metadata = {
            'source': filename,
            'type': 'unknown'
        }
        
        # Detectar tipo de documento
        if 'PRODUCTO:' in content:
            metadata['type'] = 'producto_veterinario'
            # Extraer nombre del producto
            for line in content.split('\n'):
                if line.startswith('PRODUCTO:'):
                    metadata['product_name'] = line.replace('PRODUCTO:', '').strip()
                elif line.startswith('CATEGORÍA:'):
                    metadata['category'] = line.replace('CATEGORÍA:', '').strip()
        elif 'PREGUNTA FRECUENTE' in content or 'FAQ' in filename.upper():
            metadata['type'] = 'pregunta_frecuente'
            metadata['category'] = 'FAQ'
        
        return metadata
    
    def build_chromadb(self, documentos: List[Dict]):
        """Construir base de datos vectorial ChromaDB"""
        print(f"🔨 Construyendo ChromaDB...")
        print(f"   Ruta: {self.chroma_path}")
        print(f"   Collection: {self.collection_name}")
        print(f"   Modelo embeddings: {self.embedding_model_name}\n")
        
        # Crear directorio si no existe
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Cargar modelo de embeddings
        print(f"🧠 Cargando modelo de embeddings...")
        embedding_model = SentenceTransformer(self.embedding_model_name)
        print(f"✅ Modelo cargado\n")
        
        # Generar embeddings
        print(f"🔢 Generando embeddings para {len(documentos)} documentos...")
        texts = [doc['text'] for doc in documentos]
        embeddings = embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        print(f"✅ Embeddings generados\n")
        
        # Crear cliente ChromaDB
        print(f"💾 Creando ChromaDB...")
        client = chromadb.PersistentClient(path=str(self.chroma_path))
        
        # Eliminar collection si existe (para rebuild limpio)
        try:
            client.delete_collection(name=self.collection_name)
            print(f"   ℹ️  Collection existente eliminada")
        except:
            pass
        
        # Crear nueva collection
        collection = client.create_collection(
            name=self.collection_name,
            metadata={"description": "Productos y FAQs de Laboratorio Chinfield"}
        )
        
        # Preparar datos para inserción
        ids = [f"doc_{i:03d}" for i in range(len(documentos))]
        metadatas = [doc['metadata'] for doc in documentos]
        
        # Insertar documentos
        collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"✅ ChromaDB creada con {collection.count()} documentos\n")
        
        # Verificación
        self._verify_database(collection)
    
    def _verify_database(self, collection):
        """Verificar que la base de datos se creó correctamente"""
        print(f"🔍 Verificando base de datos...")
        
        count = collection.count()
        print(f"   Total documentos: {count}")
        
        # Obtener algunos documentos de muestra
        sample = collection.get(limit=3)
        print(f"   Documentos de muestra:")
        for i, (doc_id, metadata) in enumerate(zip(sample['ids'], sample['metadatas'])):
            print(f"      {i+1}. {doc_id} - {metadata.get('product_name', metadata.get('source'))}")
        
        print(f"✅ Verificación completada\n")
    
    def generate_build_info(self, documentos: List[Dict]):
        """Generar archivo de información del build"""
        info = {
            'build_timestamp': str(Path(self.chroma_path).stat().st_mtime),
            'total_documents': len(documentos),
            'embedding_model': self.embedding_model_name,
            'collection_name': self.collection_name,
            'documents': [
                {
                    'filename': doc['filename'],
                    'type': doc['metadata']['type'],
                    'source': doc['metadata']['source']
                }
                for doc in documentos
            ]
        }
        
        info_path = self.chroma_path / 'build_info.json'
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Información del build guardada en: {info_path}\n")


def main():
    """Función principal de build"""
    print("="*70)
    print("🚀 CHROMADB BUILD SCRIPT - Laboratorio Chinfield")
    print("="*70)
    print()
    
    try:
        builder = ChromaDBBuilder(
            data_dir="./data/products",
            chroma_path="./models/chroma_db",
            collection_name="chinfield_products",
            embedding_model="all-MiniLM-L6-v2"
        )
        
        # Cargar documentos
        documentos = builder.load_product_files()
        
        # Construir base de datos
        builder.build_chromadb(documentos)
        
        # Generar info del build
        builder.generate_build_info(documentos)
        
        print("="*70)
        print("✅ BUILD COMPLETADO EXITOSAMENTE")
        print("="*70)
        print()
        print("La base de datos ChromaDB está lista para deployment.")
        print(f"Ubicación: {builder.chroma_path}")
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ ERROR EN BUILD")
        print("="*70)
        print(f"\n{str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
