# 🐄 Chinfield RAG Demo - Bot de Consultas Veterinarias

Demo funcional de un asistente inteligente para Laboratorio Chinfield que responde consultas sobre productos veterinarios usando RAG (Retrieval Augmented Generation).

## 🎯 Características

- ✅ **RAG System**: Respuestas basadas en documentación real de productos
- ✅ **Derivación inteligente**: Detecta cuando no puede responder y deriva a humanos
- ✅ **Widget de chat**: Interfaz embebida lista para usar
- ✅ **Optimizado para Railway Hobby**: Funciona en plan gratuito (512MB RAM)
- ✅ **15 productos indexados**: 10 productos + 5 FAQs

## 📋 Requisitos Previos

- Python 3.11+
- Cuenta en Railway (plan Hobby)
- OpenAI API Key
- Git instalado

## 🚀 Deployment a Railway (Paso a Paso)

### 1. Preparar el Repositorio Local

```bash
# Clonar o crear directorio del proyecto
mkdir chinfield-rag-demo
cd chinfield-rag-demo

# Copiar todos los archivos del proyecto:
# - app.py
# - rag_system_api.py
# - build_chromadb.py
# - requirements.txt
# - nixpacks.toml
# - Procfile
# - runtime.txt
# - .gitignore
# - config/settings.py
# - data/products/*.txt (15 archivos)
```

### 2. Inicializar Git

```bash
git init
git add .
git commit -m "Initial commit - Chinfield RAG Demo"
```

### 3. Testing Local (IMPORTANTE)

Antes de deployar, validar localmente:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar OpenAI API Key
export OPENAI_API_KEY='tu-api-key-aqui'

# Ejecutar tests
python test_local.py

# Si todos los tests pasan, continuar
```

### 4. Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Conecta tu repositorio (o usa "Deploy from local")

### 5. Configurar Variables de Entorno en Railway

En el dashboard de Railway:

1. Ve a **Variables** tab
2. Agrega:
   ```
   OPENAI_API_KEY=sk-tu-api-key-aqui
   ```

### 6. Deploy

Railway detectará automáticamente `nixpacks.toml` y:
- Instalará dependencias
- Ejecutará `build_chromadb.py` (indexa los 15 productos)
- Arrancará la app con uvicorn

El proceso toma ~3-5 minutos.

### 7. Verificar Deployment

Una vez deployado, Railway te dará una URL:

```
https://tu-app.up.railway.app
```

Prueba:
- `GET /` → Widget de chat
- `GET /health` → Status del sistema
- `POST /api/chat` → Endpoint de consultas

## 🧪 Testing Local Completo

### Opción 1: Con el script de testing

```bash
python test_local.py
```

### Opción 2: Manual

```bash
# 1. Build ChromaDB
python build_chromadb.py

# 2. Arrancar servidor local
export OPENAI_API_KEY='tu-api-key'
uvicorn app:app --reload --port 8000

# 3. Abrir navegador
open http://localhost:8000
```

### Opción 3: Test de API directo

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es Biomec Plus?"}'
```

## 📁 Estructura del Proyecto

```
chinfield-rag-demo/
├── app.py                      # FastAPI app principal
├── rag_system_api.py           # Sistema RAG
├── build_chromadb.py           # Script de indexación
├── test_local.py               # Testing local
├── requirements.txt            # Dependencias Python
├── nixpacks.toml              # Config Railway
├── Procfile                   # Comando de inicio
├── runtime.txt                # Versión Python
├── .gitignore                 # Archivos ignorados
├── config/
│   └── settings.py            # Configuración del sistema
├── data/
│   └── products/              # 15 archivos de productos
│       ├── producto_01_Biomec_Plus.txt
│       ├── producto_02_Terramicina_LA.txt
│       └── ... (13 más)
└── models/
    └── chroma_db/             # BD vectorial (generada en build)
        ├── .gitkeep
        └── [generado en runtime]
```

## 🔧 Configuración Técnica

### Stack Tecnológico

- **Framework**: FastAPI
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: ChromaDB
- **Deployment**: Railway

### Optimizaciones para Railway Hobby (512MB RAM)

- ✅ Modelo de embeddings ligero (~120MB)
- ✅ Lazy loading del RAG system
- ✅ ChromaDB pre-construida en build phase
- ✅ Modo read-only (no escribe en runtime)
- ✅ Solo 3 documentos por query

### Variables de Configuración

En `config/settings.py`:

```python
# Preset Demo (usado en Railway)
default_k = 3                    # Documentos a recuperar
confidence_threshold = 0.65      # Umbral para derivar a humano
default_temperature = 0.7        # Temperatura OpenAI
default_max_tokens = 500         # Tokens máximos respuesta
```

## 💬 Derivación a Humano

El sistema detecta automáticamente cuando debe derivar:

**Criterios:**
1. Confianza promedio < 0.65
2. No se encontraron documentos relevantes
3. Error en generación de respuesta

**Respuesta con derivación:**
```
[Respuesta del bot]

---

💬 ¿Necesitás más ayuda?

Para consultas específicas contactá:
📧 info@chinfield.com
📞 +54 11 XXXX-XXXX
🌐 https://chinfield.com/contacto
```

## 🐛 Troubleshooting

### Error: "ChromaDB no encontrada"

```bash
# Ejecutar build manualmente
python build_chromadb.py
```

### Error: "OPENAI_API_KEY no configurada"

```bash
# Railway: agregar en Variables tab
# Local:
export OPENAI_API_KEY='tu-key'
```

### Error: "Module not found"

```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

### Error de memoria en Railway

- Verifica que estás usando el modelo `all-MiniLM-L6-v2` (ligero)
- Revisa logs en Railway dashboard
- Considera upgrade a plan Pro si necesario

## 📊 Métricas de Performance

**Build Time**: ~2-3 minutos
- Install dependencies: 1-2 min
- Build ChromaDB: 30-60 seg

**Runtime**:
- Cold start: ~5-8 seg
- Query response: ~2-4 seg
- RAM usage: ~300-400 MB

## 🔐 Seguridad

- ✅ CORS configurado (solo para demo)
- ✅ No se exponen secrets en código
- ✅ Variables de entorno para API keys
- ⚠️ Para producción: agregar rate limiting y autenticación

## 📝 Próximos Pasos (Roadmap)

**Para convertir en producción:**

1. **Escalabilidad**
   - Migrar a BD vectorial cloud (Pinecone/Qdrant)
   - Agregar cache de respuestas
   - Implementar rate limiting

2. **Funcionalidades**
   - Historial de conversaciones
   - Multi-idioma
   - Integración con WhatsApp/Telegram

3. **Monitoreo**
   - Logging estructurado
   - Analytics de consultas
   - Alertas de errores

4. **Contenido**
   - Indexar catálogo completo (~100+ productos)
   - Agregar PDFs técnicos
   - Videos y contenido multimedia

## 🤝 Contacto

**Demo creada para:** Laboratorio Chinfield
**Desarrollador:** [Tu nombre]
**Fecha:** Noviembre 2024

---

## 📄 Licencia

Este es un proyecto demo/propuesta. No afiliado oficialmente con Laboratorio Chinfield S.A.

Para información oficial visita: [chinfield.com](https://chinfield.com)
