# ✅ CHECKLIST DE DEPLOYMENT - Chinfield RAG Demo

## Pre-Deployment (Local)

### 1. Archivos del Proyecto
- [ ] `app.py` - API principal actualizada (sin auto-init)
- [ ] `rag_system_api.py` - Sistema RAG
- [ ] `build_chromadb.py` - Script de indexación
- [ ] `test_local.py` - Script de testing
- [ ] `requirements.txt` - Todas las dependencias
- [ ] `nixpacks.toml` - Con fase de build configurada
- [ ] `Procfile` - Comando de inicio
- [ ] `runtime.txt` - Python 3.11.9
- [ ] `.gitignore` - Configurado correctamente
- [ ] `README.md` - Documentación completa

### 2. Estructura de Directorios
- [ ] `config/settings.py` existe
- [ ] `data/products/` contiene 15 archivos .txt
- [ ] `models/chroma_db/` tiene .gitkeep

### 3. Validación Local
```bash
# Ejecutar cada comando y verificar
python test_local.py          # ¿Todos los tests pasan?
python build_chromadb.py      # ¿ChromaDB se crea sin errores?
export OPENAI_API_KEY='...'   # ¿API key configurada?
uvicorn app:app --port 8000   # ¿App arranca correctamente?
```

- [ ] Todos los tests de `test_local.py` pasan
- [ ] ChromaDB se construye con 15 documentos
- [ ] API arranca sin errores
- [ ] Widget de chat funciona en localhost:8000
- [ ] Query de prueba responde correctamente

### 4. Git
```bash
git init
git add .
git commit -m "Initial commit"
```

- [ ] Repositorio Git inicializado
- [ ] Todos los archivos commiteados
- [ ] .gitignore funcionando (no commitea venv/, __pycache__, etc)

---

## Deployment a Railway

### 5. Cuenta Railway
- [ ] Cuenta creada en railway.app
- [ ] Plan Hobby activo ($5 crédito/mes)
- [ ] GitHub conectado (opcional)

### 6. Crear Proyecto
- [ ] Nuevo proyecto creado en Railway
- [ ] Repositorio conectado (GitHub o local)
- [ ] Railway detectó nixpacks.toml

### 7. Variables de Entorno
En Railway Dashboard → Variables:
- [ ] `OPENAI_API_KEY` configurada

### 8. Deploy Inicial
- [ ] Push a GitHub o deploy desde Railway CLI
- [ ] Build inició automáticamente
- [ ] Fase "install" completada (~1-2 min)
- [ ] Fase "build" completada (~30-60 seg)
  - [ ] build_chromadb.py ejecutado
  - [ ] 15 documentos indexados
- [ ] Fase "start" completada
- [ ] App corriendo

### 9. Verificación Post-Deploy
Obtener URL de Railway (ej: https://chinfield-rag.up.railway.app)

```bash
# Health check
curl https://tu-url.railway.app/health

# Debe retornar:
# {"status": "healthy", "version": "2.0.0", "chromadb_ready": true}
```

- [ ] `/health` responde correctamente
- [ ] `chromadb_ready: true`
- [ ] Página principal (`/`) carga el widget
- [ ] Chat widget responde a consultas

### 10. Testing Funcional
Probar en la UI web:
- [ ] "¿Qué es Biomec Plus?" → Responde con info del producto
- [ ] "¿Cuál es la dosificación de Terramicina?" → Responde correctamente
- [ ] "¿Qué es el tiempo de retiro?" → Usa FAQ
- [ ] "¿Cuánto cuesta el producto?" → Deriva a humano (no tiene esa info)

---

## Post-Deployment

### 11. Monitoreo Inicial
En Railway Dashboard:
- [ ] Revisar logs de build
- [ ] Revisar logs de runtime
- [ ] Verificar uso de memoria (<400MB)
- [ ] Verificar uso de CPU

### 12. Documentación para Cliente
- [ ] URL de la demo documentada
- [ ] Capturas de pantalla tomadas
- [ ] Video demo grabado (opcional)
- [ ] Documento de propuesta preparado

### 13. Backup
- [ ] Código en GitHub/GitLab
- [ ] Variables de entorno respaldadas
- [ ] Configuración de Railway documentada

---

## Checklist de Troubleshooting

Si algo falla, verificar:

### Build Failed
- [ ] Verificar logs en Railway
- [ ] ¿nixpacks.toml tiene sintaxis correcta?
- [ ] ¿requirements.txt tiene todas las dependencias?
- [ ] ¿data/products/ tiene los archivos?

### Runtime Failed
- [ ] ¿OPENAI_API_KEY configurada?
- [ ] ¿ChromaDB se creó en build phase?
- [ ] ¿Logs muestran errores específicos?
- [ ] ¿Puerto $PORT está siendo usado?

### API No Responde
- [ ] ¿Health check funciona?
- [ ] ¿Logs muestran "RAG System listo"?
- [ ] ¿OpenAI API key es válida?
- [ ] ¿Hay límites de rate en OpenAI?

### Memoria Insuficiente
- [ ] ¿Modelo de embeddings es all-MiniLM-L6-v2?
- [ ] ¿Lazy loading está activado?
- [ ] ¿ChromaDB es read-only?
- [ ] Considerar upgrade a Railway Pro

---

## ✅ DEPLOYMENT EXITOSO

Si completaste todos los checkpoints:

🎉 **¡FELICITACIONES!**

Tu demo está lista para mostrar a Chinfield:
- URL: https://tu-app.railway.app
- Status: ✅ Funcionando
- Costo: $0 (Railway Hobby plan)

**Próximos pasos sugeridos:**
1. Preparar presentación con la demo
2. Documentar costos de escalamiento
3. Propuesta de funcionalidades adicionales
4. Roadmap de desarrollo

---

**Fecha de deployment:** _________________
**URL final:** _________________
**Notas:** _________________
