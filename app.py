"""
API Backend para Demo Chinfield
FastAPI + RAG System - Optimizado para Railway Hobby Plan
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
    needs_human: Optional[bool] = False  # Nuevo campo para derivación

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
    # Si hay error en la generación
    if not result.get('success', False):
        return True
    
    # Verificar confianza promedio de documentos
    docs = result.get('retrieved_docs', [])
    if docs:
        avg_similarity = sum(doc['similarity'] for doc in docs) / len(docs)
        if avg_similarity < config.confidence_threshold:
            return True
    
    # Si no se encontraron documentos relevantes
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

@app.get("/")
async def root():
    """Página principal con widget de chat"""
    html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asistente Inteligente Chinfield | Demo IA Veterinaria</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --verde-chinfield: #2d8659;
            --verde-oscuro: #1f5a3d;
            --verde-claro: #4da776;
            --gris-oscuro: #2c3e50;
            --gris-medio: #5a6c7d;
            --gris-claro: #e8eef2;
            --blanco: #ffffff;
            --amarillo: #f4a030;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Roboto', sans-serif; 
            background: var(--gris-claro); 
            color: var(--gris-oscuro);
            line-height: 1.6;
        }
        
        /* HEADER */
        .header {
            background: var(--blanco);
            border-bottom: 3px solid var(--verde-chinfield);
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo-area {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--verde-chinfield), var(--verde-claro));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(45, 134, 89, 0.3);
        }
        
        .brand-text h1 {
            font-family: 'Montserrat', sans-serif;
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--verde-chinfield);
            letter-spacing: -0.5px;
            margin-bottom: -4px;
        }
        
        .brand-text .tagline {
            font-size: 0.85rem;
            color: var(--gris-medio);
            font-weight: 400;
        }
        
        .demo-pill {
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            color: #92400e;
            padding: 0.5rem 1.2rem;
            border-radius: 30px;
            font-size: 0.8rem;
            font-weight: 600;
            border: 2px solid #f59e0b;
            box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
        }
        
        /* HERO */
        .hero {
            background: linear-gradient(135deg, var(--verde-chinfield) 0%, var(--verde-oscuro) 100%);
            color: var(--blanco);
            padding: 5rem 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 50%;
            height: 100%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="rgba(255,255,255,0.05)"/></svg>');
            background-size: 200px;
            opacity: 0.3;
        }
        
        .hero-content {
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
        }
        
        .hero-text h2 {
            font-family: 'Montserrat', sans-serif;
            font-size: 3.2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 1.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .hero-text p {
            font-size: 1.25rem;
            opacity: 0.95;
            margin-bottom: 2rem;
            line-height: 1.8;
        }
        
        .hero-stats {
            display: flex;
            gap: 3rem;
            margin-top: 2rem;
        }
        
        .stat-item {
            text-align: left;
        }
        
        .stat-number {
            font-family: 'Montserrat', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--amarillo);
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .hero-visual {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 3rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .hero-features {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .hero-feature-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            background: rgba(255,255,255,0.15);
            padding: 1rem 1.5rem;
            border-radius: 12px;
        }
        
        .hero-feature-icon {
            font-size: 2rem;
        }
        
        /* CTA BUTTON */
        .cta-primary {
            background: var(--amarillo);
            color: var(--gris-oscuro);
            padding: 1.2rem 3rem;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 6px 20px rgba(244, 160, 48, 0.4);
            font-family: 'Montserrat', sans-serif;
        }
        
        .cta-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(244, 160, 48, 0.6);
            background: #ff9800;
        }
        
        /* COMO FUNCIONA */
        .how-it-works {
            background: var(--blanco);
            padding: 5rem 2rem;
        }
        
        .section-title {
            text-align: center;
            font-family: 'Montserrat', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--gris-oscuro);
            margin-bottom: 1rem;
        }
        
        .section-subtitle {
            text-align: center;
            color: var(--gris-medio);
            font-size: 1.1rem;
            margin-bottom: 4rem;
        }
        
        .steps-container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 3rem;
        }
        
        .step-card {
            text-align: center;
            padding: 2.5rem 2rem;
            border-radius: 16px;
            background: var(--gris-claro);
            transition: all 0.3s ease;
            position: relative;
        }
        
        .step-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 30px rgba(45, 134, 89, 0.15);
        }
        
        .step-number {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--verde-chinfield), var(--verde-claro));
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0 auto 1.5rem;
            box-shadow: 0 4px 12px rgba(45, 134, 89, 0.3);
        }
        
        .step-card h3 {
            font-family: 'Montserrat', sans-serif;
            font-size: 1.4rem;
            color: var(--gris-oscuro);
            margin-bottom: 1rem;
        }
        
        .step-card p {
            color: var(--gris-medio);
            line-height: 1.7;
        }
        
        /* CASOS DE USO */
        .use-cases {
            background: var(--gris-claro);
            padding: 5rem 2rem;
        }
        
        .cases-grid {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 2rem;
        }
        
        .case-card {
            background: var(--blanco);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }
        
        .case-card:hover {
            border-color: var(--verde-chinfield);
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(45, 134, 89, 0.2);
        }
        
        .case-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .case-card h4 {
            font-family: 'Montserrat', sans-serif;
            font-size: 1.1rem;
            color: var(--gris-oscuro);
            margin-bottom: 0.5rem;
        }
        
        .case-card p {
            font-size: 0.9rem;
            color: var(--gris-medio);
        }
        
        /* CTA SECTION */
        .cta-section {
            background: linear-gradient(135deg, var(--verde-oscuro), var(--verde-chinfield));
            padding: 5rem 2rem;
            text-align: center;
            color: var(--blanco);
        }
        
        .cta-section h2 {
            font-family: 'Montserrat', sans-serif;
            font-size: 2.8rem;
            font-weight: 800;
            margin-bottom: 1rem;
        }
        
        .cta-section p {
            font-size: 1.2rem;
            opacity: 0.95;
            margin-bottom: 2.5rem;
        }
        
        /* FOOTER */
        .footer {
            background: var(--gris-oscuro);
            color: var(--gris-claro);
            padding: 3rem 2rem 2rem;
        }
        
        .footer-content {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 4rem;
            margin-bottom: 2rem;
        }
        
        .footer-section h3 {
            font-family: 'Montserrat', sans-serif;
            color: var(--verde-claro);
            margin-bottom: 1rem;
        }
        
        .footer-section p, .footer-section a {
            color: var(--gris-claro);
            text-decoration: none;
            display: block;
            margin-bottom: 0.5rem;
        }
        
        .footer-section a:hover {
            color: var(--verde-claro);
        }
        
        .footer-bottom {
            max-width: 1400px;
            margin: 0 auto;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            text-align: center;
            font-size: 0.85rem;
            opacity: 0.7;
        }
        
        .disclaimer-highlight {
            color: var(--amarillo);
            font-weight: 600;
        }
        
        /* CHAT WIDGET */
        #chat-widget-button {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, var(--verde-chinfield), var(--verde-claro));
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 32px;
            cursor: pointer;
            box-shadow: 0 6px 24px rgba(45, 134, 89, 0.4);
            z-index: 9998;
            transition: all 0.3s ease;
        }
        
        #chat-widget-button:hover {
            transform: scale(1.1) rotate(5deg);
            box-shadow: 0 8px 32px rgba(45, 134, 89, 0.6);
        }
        
        #chat-widget-container {
            position: fixed;
            bottom: 100px;
            right: 24px;
            width: 420px;
            height: 640px;
            background: var(--blanco);
            border-radius: 20px;
            box-shadow: 0 12px 48px rgba(0,0,0,0.2);
            z-index: 9999;
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 2px solid var(--verde-chinfield);
        }
        
        #chat-header {
            background: linear-gradient(135deg, var(--verde-chinfield), var(--verde-claro));
            color: white;
            padding: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-avatar {
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-right: 12px;
        }
        
        .chat-header-info {
            display: flex;
            align-items: center;
            flex: 1;
        }
        
        .chat-title {
            font-weight: 700;
            font-size: 1.1rem;
        }
        
        .chat-status {
            font-size: 0.8rem;
            opacity: 0.9;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        #chat-close {
            cursor: pointer;
            font-size: 24px;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
        }
        
        #chat-close:hover {
            background: rgba(255,255,255,0.2);
        }
        
        #chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafb;
        }
        
        .message {
            margin: 12px 0;
            padding: 12px 16px;
            border-radius: 16px;
            max-width: 85%;
            animation: slideIn 0.3s ease;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        
        .message-user {
            background: var(--verde-chinfield);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .message-assistant {
            background: white;
            color: var(--gris-oscuro);
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .typing {
            display: flex;
            gap: 6px;
            padding: 12px 16px;
            background: white;
            border-radius: 16px;
            width: fit-content;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--verde-chinfield);
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        
        #chat-input-area {
            border-top: 1px solid #e5e7eb;
            padding: 16px;
            display: flex;
            gap: 10px;
            background: white;
        }
        
        #chat-input {
            flex: 1;
            border: 2px solid #e5e7eb;
            border-radius: 24px;
            padding: 12px 18px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }
        
        #chat-input:focus {
            border-color: var(--verde-chinfield);
        }
        
        #chat-send {
            background: var(--verde-chinfield);
            color: white;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        
        #chat-send:hover {
            background: var(--verde-oscuro);
            transform: scale(1.05);
        }
        
        #chat-send:disabled {
            background: #d1d5db;
            cursor: not-allowed;
        }
        
        /* RESPONSIVE */
        @media (max-width: 1200px) {
            .hero-content { grid-template-columns: 1fr; }
            .hero-visual { display: none; }
            .steps-container { grid-template-columns: 1fr; }
            .cases-grid { grid-template-columns: repeat(2, 1fr); }
            .footer-content { grid-template-columns: 1fr; }
        }
        
        @media (max-width: 768px) {
            .hero-text h2 { font-size: 2rem; }
            .section-title { font-size: 1.8rem; }
            .cases-grid { grid-template-columns: 1fr; }
            #chat-widget-container {
                width: 100%;
                height: 100%;
                bottom: 0;
                right: 0;
                border-radius: 0;
            }
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <div class="header">
        <div class="header-content">
            <div class="logo-area">
                <div class="logo-icon">🐄</div>
                <div class="brand-text">
                    <h1>CHINFIELD</h1>
                    <div class="tagline">Asistente Inteligente Veterinario</div>
                </div>
            </div>
            <div class="demo-pill">⚡ DEMO TÉCNICA</div>
        </div>
    </div>

    <!-- HERO -->
    <div class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h2>Asistencia Veterinaria Inteligente 24/7</h2>
                <p>Consultas instantáneas sobre productos veterinarios con inteligencia artificial. Dosificaciones, indicaciones y recomendaciones técnicas al instante.</p>
                <button class="cta-primary" onclick="openChat()">Iniciar Consulta Ahora →</button>
                <div class="hero-stats">
                    <div class="stat-item">
                        <div class="stat-number">15+</div>
                        <div class="stat-label">Productos indexados</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">24/7</div>
                        <div class="stat-label">Disponibilidad</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">&lt;3s</div>
                        <div class="stat-label">Tiempo de respuesta</div>
                    </div>
                </div>
            </div>
            <div class="hero-visual">
                <div class="hero-features">
                    <div class="hero-feature-item">
                        <div class="hero-feature-icon">💊</div>
                        <div>
                            <strong>Información Técnica</strong><br>
                            <small>Fichas completas de productos</small>
                        </div>
                    </div>
                    <div class="hero-feature-item">
                        <div class="hero-feature-icon">🎯</div>
                        <div>
                            <strong>Respuestas Precisas</strong><br>
                            <small>Basadas en documentación oficial</small>
                        </div>
                    </div>
                    <div class="hero-feature-item">
                        <div class="hero-feature-icon">👨‍⚕️</div>
                        <div>
                            <strong>Derivación Inteligente</strong><br>
                            <small>Conecta con expertos cuando es necesario</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- COMO FUNCIONA -->
    <div class="how-it-works">
        <h2 class="section-title">¿Cómo Funciona?</h2>
        <p class="section-subtitle">Tres pasos simples para obtener información veterinaria precisa</p>
        <div class="steps-container">
            <div class="step-card">
                <div class="step-number">1</div>
                <h3>Hacé tu Consulta</h3>
                <p>Escribí tu pregunta sobre dosificaciones, indicaciones, tiempos de retiro o cualquier aspecto técnico de nuestros productos.</p>
            </div>
            <div class="step-card">
                <div class="step-number">2</div>
                <h3>IA Busca y Analiza</h3>
                <p>Nuestro sistema analiza la documentación técnica oficial y encuentra la información más relevante en segundos.</p>
            </div>
            <div class="step-card">
                <div class="step-number">3</div>
                <h3>Recibí la Respuesta</h3>
                <p>Obtené respuestas precisas basadas en fichas técnicas. Si es necesario, te conectamos con un especialista.</p>
            </div>
        </div>
    </div>

    <!-- CASOS DE USO -->
    <div class="use-cases">
        <h2 class="section-title">Ideal Para</h2>
        <p class="section-subtitle">Profesionales y productores del sector veterinario</p>
        <div class="cases-grid">
            <div class="case-card">
                <div class="case-icon">👨‍⚕️</div>
                <h4>Veterinarios</h4>
                <p>Consultas rápidas durante la práctica clínica</p>
            </div>
            <div class="case-card">
                <div class="case-icon">🏢</div>
                <h4>Distribuidores</h4>
                <p>Información técnica para clientes</p>
            </div>
            <div class="case-card">
                <div class="case-icon">🐄</div>
                <h4>Productores</h4>
                <p>Dosificaciones y aplicaciones en campo</p>
            </div>
            <div class="case-card">
                <div class="case-icon">🎓</div>
                <h4>Estudiantes</h4>
                <p>Material de estudio y consulta</p>
            </div>
        </div>
    </div>

    <!-- CTA -->
    <div class="cta-section">
        <h2>Probá el Asistente Ahora</h2>
        <p>Experimentá la próxima generación de consultas veterinarias</p>
        <button class="cta-primary" onclick="openChat()">Iniciar Consulta Gratuita →</button>
    </div>

    <!-- FOOTER -->
    <div class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h3>Sobre Este Demo</h3>
                <p>Demostración técnica de un sistema de inteligencia artificial aplicado a consultas veterinarias. Desarrollado con tecnología RAG (Retrieval-Augmented Generation) para proporcionar respuestas precisas basadas en documentación oficial.</p>
            </div>
            <div class="footer-section">
                <h3>Tecnología</h3>
                <p>• OpenAI GPT-4</p>
                <p>• ChromaDB</p>
                <p>• FastAPI</p>
                <p>• Sentence Transformers</p>
            </div>
            <div class="footer-section">
                <h3>Contacto Oficial</h3>
                <p>Para información real de productos:</p>
                <a href="https://chinfield.com" target="_blank">→ chinfield.com</a>
                <a href="mailto:info@chinfield.com">→ info@chinfield.com</a>
            </div>
        </div>
        <div class="footer-bottom">
            <p><span class="disclaimer-highlight">IMPORTANTE:</span> Esta es una demostración técnica independiente, no afiliada oficialmente con Laboratorio Chinfield S.A. Para consultas reales, visite <a href="https://chinfield.com" target="_blank" style="color: var(--verde-claro);">chinfield.com</a></p>
        </div>
    </div>

    <!-- CHAT WIDGET -->
    <button id="chat-widget-button" onclick="toggleChat()">💬</button>
    <div id="chat-widget-container">
        <div id="chat-header">
            <div class="chat-header-info">
                <div class="chat-avatar">🐄</div>
                <div>
                    <div class="chat-title">Asistente Chinfield</div>
                    <div class="chat-status">
                        <span class="status-dot"></span>
                        En línea • Demo
                    </div>
                </div>
            </div>
            <div id="chat-close" onclick="toggleChat()">✕</div>
        </div>
        <div id="chat-messages">
            <div class="message message-assistant">¡Hola! Soy tu asistente veterinario inteligente. Puedo responder consultas sobre productos, dosificaciones, indicaciones y más. ¿En qué puedo ayudarte?</div>
        </div>
        <div id="chat-input-area">
            <input type="text" id="chat-input" placeholder="Escribe tu consulta..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button id="chat-send" onclick="sendMessage()">➤</button>
        </div>
    </div>

    <script>
        function toggleChat(){const c=document.getElementById('chat-widget-container'),b=document.getElementById('chat-widget-button');if(c.style.display==='none'||!c.style.display){c.style.display='flex';b.style.display='none';document.getElementById('chat-input').focus();}else{c.style.display='none';b.style.display='flex';}}
        function openChat(){document.getElementById('chat-widget-container').style.display='flex';document.getElementById('chat-widget-button').style.display='none';document.getElementById('chat-input').focus();}
        function addMessage(r,c){const d=document.getElementById('chat-messages'),m=document.createElement('div');m.className='message message-'+r;m.textContent=c;d.appendChild(m);d.scrollTop=d.scrollHeight;}
        function showTyping(){const d=document.getElementById('chat-messages'),t=document.createElement('div');t.id='typing-indicator';t.className='typing';t.innerHTML='<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';d.appendChild(t);d.scrollTop=d.scrollHeight;}
        function hideTyping(){const t=document.getElementById('typing-indicator');if(t)t.remove();}
        async function sendMessage(){const i=document.getElementById('chat-input'),s=document.getElementById('chat-send'),m=i.value.trim();if(!m)return;i.disabled=true;s.disabled=true;addMessage('user',m);i.value='';showTyping();try{const r=await fetch(window.location.origin+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});const d=await r.json();hideTyping();if(d.success){addMessage('assistant',d.answer);}else{addMessage('assistant','Disculpá, hubo un error. Por favor contactá a info@chinfield.com');}}catch(e){hideTyping();addMessage('assistant','Error de conexión. Por favor intentá nuevamente.');console.error(e);}i.disabled=false;s.disabled=false;i.focus();}
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

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
        result = rag.query(request.message, verbose=True)
        print(f"🔍 RAG Result: {result}")
        
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)