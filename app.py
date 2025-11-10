"""
API Backend para Demo Chinfield
FastAPI + RAG System - Optimizado para Railway Hobby Plan
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import traceback

from rag_system_api import RAGSystemAPI
from config.settings import ConfigPresets

# =============================================================================
# CONFIGURACIÓN FASTAPI
# =============================================================================

app = FastAPI(
    title="Chinfield Demo API",
    description="API para asistente técnico veterinario Chinfield",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración RAG (modo demo - optimizado para Railway)
config = ConfigPresets.demo()

# LAZY LOADING del RAG System (optimización de memoria)
rag_system = None

def get_rag():
    """Inicializar RAG solo cuando se necesita (lazy loading)"""
    global rag_system
    if rag_system is None:
        print("🚀 Inicializando RAG System...")
        
        # Validar que ChromaDB existe
        if not os.path.exists(config.chroma_db_path):
            raise Exception(
                f"❌ ChromaDB no encontrada en {config.chroma_db_path}. "
                "Ejecutar build_chromadb.py primero."
            )
        
        rag_system = RAGSystemAPI(
            config=config,
            use_openai=True,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model="gpt-4o-mini"
        )
        print("✅ RAG System listo\n")
    return rag_system

# =============================================================================
# MODELOS
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    success: bool
    num_docs: int
    model: str
    needs_human: Optional[bool] = False

# =============================================================================
# LÓGICA DE DERIVACIÓN A HUMANO
# =============================================================================

def should_handoff_to_human(result: dict, config) -> bool:
    """
    Determinar si se debe derivar a un humano
    
    Criterios:
    1. Baja confianza en documentos recuperados
    2. Pregunta fuera del dominio de productos veterinarios
    3. Error en generación de respuesta
    """
    if not result.get('success', False):
        return True
    
    docs = result.get('retrieved_docs', [])
    if docs:
        avg_similarity = sum(doc['similarity'] for doc in docs) / len(docs)
        if avg_similarity < config.confidence_threshold:
            return True
    
    if len(docs) == 0:
        return True
    
    return False

def add_human_handoff_message(answer: str) -> str:
    """Agregar mensaje de derivación a humano"""
    handoff_msg = "\n\n---\n\n💬 **¿Necesitás más ayuda?**\n\n"
    handoff_msg += "Para consultas específicas o asesoramiento personalizado, "
    handoff_msg += "contactá a nuestro equipo técnico:\n\n"
    handoff_msg += "📧 Email: info@chinfield.com\n"
    handoff_msg += "📞 Teléfono: +54 11 XXXX-XXXX\n"
    handoff_msg += "🌐 Web: https://chinfield.com/contacto"
    
    return answer + handoff_msg

# =============================================================================
# ENDPOINTS  
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "chromadb_ready": os.path.exists(config.chroma_db_path)
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal de chat con derivación inteligente a humanos
    """
    try:
        # Obtener RAG system
        rag = get_rag()
        
        # Ejecutar query
        result = rag.query(request.message, verbose=False)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail="Error generando respuesta")
        
        # Determinar si derivar a humano
        needs_handoff = should_handoff_to_human(result, config)
        
        # Agregar mensaje de contacto si es necesario
        answer = result['answer']
        if needs_handoff:
            answer = add_human_handoff_message(answer)
        
        return ChatResponse(
            answer=answer,
            success=True,
            num_docs=result['num_docs_used'],
            model=result['model'],
            needs_human=needs_handoff
        )
        
    except Exception as e:
        print(f"❌ Error en /api/chat: {e}")
        traceback.print_exc()
        
        # Respuesta de error con derivación a humano
        error_answer = (
            "Disculpá, hubo un problema procesando tu consulta. "
            "Te recomiendo contactar directamente a nuestro equipo técnico:\n\n"
            "📧 info@chinfield.com\n"
            "🌐 https://chinfield.com/contacto"
        )
        
        return ChatResponse(
            answer=error_answer,
            success=False,
            num_docs=0,
            model="error",
            needs_human=True
        )

# =============================================================================
# SERVIR ARCHIVOS ESTÁTICOS DEL FRONTEND
# =============================================================================

# Montar carpeta frontend como archivos estáticos
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)