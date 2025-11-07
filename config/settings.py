"""
Configuración del Sistema RAG - Optimizado para Railway Hobby Plan
Versión simplificada sin dependencias externas
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RAGConfig:
    """Configuración del sistema RAG"""
    
    # ChromaDB
    chroma_db_path: str = "./models/chroma_db"
    collection_name: str = "chinfield_products"
    
    # Modelo de embeddings (optimizado para RAM limitada)
    embedding_model: str = "all-MiniLM-L6-v2"  # ~120MB RAM
    
    # OpenAI API
    openai_model: str = "gpt-4o-mini"
    default_temperature: float = 0.7
    default_max_tokens: int = 500
    
    # Retrieval
    default_k: int = 3  # Documentos a recuperar por defecto
    
    # Ollama (fallback - no usado en Railway)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # Prompt strategy (opcional)
    prompt_strategy: Optional[str] = None
    
    # Umbral de confianza para derivar a humano
    confidence_threshold: float = 0.65


# Instancia por defecto
DEFAULT_CONFIG = RAGConfig()


# Configuraciones alternativas para diferentes entornos
class ConfigPresets:
    """Presets de configuración para diferentes escenarios"""
    
    @staticmethod
    def production() -> RAGConfig:
        """Configuración para producción"""
        return RAGConfig(
            default_temperature=0.5,  # Más conservador
            default_max_tokens=600,
            default_k=5,
            confidence_threshold=0.70
        )
    
    @staticmethod
    def development() -> RAGConfig:
        """Configuración para desarrollo local"""
        return RAGConfig(
            default_temperature=0.7,
            default_max_tokens=800,
            default_k=3,
            confidence_threshold=0.60
        )
    
    @staticmethod
    def demo() -> RAGConfig:
        """Configuración para demo (Railway Hobby)"""
        return RAGConfig(
            chroma_db_path="./models/chroma_db",
            embedding_model="all-MiniLM-L6-v2",  # Modelo ligero
            default_temperature=0.7,
            default_max_tokens=500,
            default_k=3,
            confidence_threshold=0.65
        )
