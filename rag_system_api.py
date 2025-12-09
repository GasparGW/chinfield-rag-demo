"""
RAG System para Chinfield - Compatible con OpenAI API
Versión adaptada para deployment en cloud
"""

import os
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime

# OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Ollama (fallback)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Config system
try:
    from config.settings import RAGConfig, DEFAULT_CONFIG
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Prompts
try:
    from prompts.strategies import PromptFactory, PromptType
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False


class RAGSystemAPI:
    """Sistema RAG compatible con OpenAI API y Ollama"""
    
    def __init__(
        self, 
        config: Optional['RAGConfig'] = None,
        use_openai: bool = True,  # ← NUEVO: elegir API
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini"
    ):
        """
        Inicializar RAG con soporte para OpenAI o Ollama
        
        Args:
            config: Configuración del sistema
            use_openai: True = OpenAI API, False = Ollama local
            openai_api_key: API key de OpenAI (o usar env var OPENAI_API_KEY)
            openai_model: Modelo de OpenAI a usar
        """
        print("🚀 Inicializando Sistema RAG...")
        
        # Configuración
        if config is not None:
            self.config = config
        elif CONFIG_AVAILABLE:
            self.config = DEFAULT_CONFIG
        else:
            raise Exception("Sistema de configuración requerido")
        
        # Modo API
        self.use_openai = use_openai
        self.openai_model = openai_model
        
        if use_openai:
            if not OPENAI_AVAILABLE:
                raise Exception("OpenAI no instalado. pip install openai")
            
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OPENAI_API_KEY requerida")
            
            self.openai_client = OpenAI(api_key=api_key)
            print(f"✅ Usando OpenAI API: {openai_model}")
        else:
            if not REQUESTS_AVAILABLE:
                raise Exception("requests no instalado")
            self.ollama_base_url = self.config.ollama_base_url
            self.ollama_model = self.config.ollama_model
            print(f"✅ Usando Ollama: {self.ollama_model}")
        
        # ChromaDB
        print(f"📦 Conectando a ChromaDB: {self.config.chroma_db_path}")
        self.chroma_client = chromadb.PersistentClient(path=self.config.chroma_db_path)
        self.collection = self.chroma_client.get_collection(name=self.config.collection_name)
        print(f"✅ Collection '{self.config.collection_name}' cargada ({self.collection.count()} docs)")
        
        # Embeddings
        print(f"📦 Cargando modelo de embeddings...")
        self.embedding_model = SentenceTransformer(self.config.embedding_model)
        print("✅ Modelo de embeddings cargado")
        
        # Prompt strategy
        if PROMPTS_AVAILABLE and self.config.prompt_strategy:
            strategy_type = PromptType[self.config.prompt_strategy.upper()]
            self.prompt_strategy = PromptFactory.get_strategy(strategy_type)
            print(f"✅ Estrategia de prompt: {self.prompt_strategy.name}")
        else:
            self.prompt_strategy = None
        
        print("✅ Sistema RAG inicializado\n")
    
    def retrieve_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Recuperar documentos relevantes"""
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        documentos = []
        if results['documents'] and results['documents'][0]:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                similarity = 1 / (1 + distance)
                documentos.append({
                    'rank': i + 1,
                    'text': doc,
                    'metadata': metadata,
                    'similarity': round(similarity, 4)
                })
        
        return documentos
    
    def generate_answer(self, query: str, context_docs: List[Dict]) -> Dict:
        """Generar respuesta usando OpenAI o Ollama"""
        
        # Construir contexto
        context = "\n\n---\n\n".join([
            f"Documento {doc['rank']}:\n{doc['text']}"
            for doc in context_docs
        ])
        
        # Construir prompt
        if self.prompt_strategy:
            prompt = self.prompt_strategy.build(context, query)
        else:
            prompt = f"""Sos un asesor técnico de Laboratorio Chinfield con 15 años de experiencia en productos veterinarios. Hablás como un colega que quiere ayudar, no como un robot.

CATÁLOGO DE PRODUCTOS CHINFIELD:
{context}

CONSULTA DEL CLIENTE:
{query}

INSTRUCCIONES DE COMPORTAMIENTO:
1. NUNCA digas "según los documentos", "no encontré información", "en la base de datos". Hablás desde tu experiencia en Chinfield.

2. Si tenemos un producto para lo que pide:
   - Recomendalo con confianza: "Para eso te recomiendo [producto]..."
   - Dá la dosificación y vía de administración
   - Mencioná contraindicaciones importantes si las hay

3. Si NO tenemos exactamente lo que pide:
   - NUNCA digas "no tenemos" o "no está en los documentos"
   - Decí algo como: "Para [problema] lo que más te puedo recomendar de nuestra línea es [producto similar]..."
   - O: "No manejamos un producto específico para eso, pero [producto] te puede servir porque..."

4. Si la consulta es sobre algo que claramente no manejamos (ej: alimento balanceado, vacunas):
   - "Eso no es parte de nuestra línea de productos, nosotros nos especializamos en [categoría]. Pero si necesitás [algo relacionado], ahí sí te puedo ayudar."

5. Usá un tono profesional pero cercano. Sos veterinario hablándole a otro profesional del sector.

6. Sé conciso. No repitas información innecesaria.

RESPUESTA:"""
        
        # Generar con OpenAI o Ollama
        if self.use_openai:
            return self._generate_openai(prompt)
        else:
            return self._generate_ollama(prompt)
    
    def _generate_openai(self, prompt: str) -> Dict:
        """Generar respuesta con OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "Sos un asesor técnico veterinario de Laboratorio Chinfield. Respondés como un empleado con experiencia, nunca mencionás 'documentos', 'base de datos' o 'información disponible'. Hablás en español rioplatense, profesional pero cercano."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.default_temperature,
                max_tokens=self.config.default_max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                'answer': answer,
                'model': self.openai_model,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'answer': f"Error: {str(e)}",
                'success': False
            }
    
    def _generate_ollama(self, prompt: str) -> Dict:
        """Generar respuesta con Ollama (fallback)"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.default_temperature,
                        "num_predict": self.config.default_max_tokens
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'answer': result.get('response', '').strip(),
                    'model': self.ollama_model,
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'answer': "Error de Ollama",
                    'success': False
                }
        except Exception as e:
            return {
                'answer': f"Error: {str(e)}",
                'success': False
            }
    
    def query(self, pregunta: str, k: int = None, verbose: bool = False) -> Dict:
        """
        Pipeline completo: retrieve + generate
        
        Args:
            pregunta: Pregunta del usuario
            k: Número de documentos a recuperar
            verbose: Mostrar logs detallados
            
        Returns:
            Dict con respuesta y metadata
        """
        k = k if k is not None else self.config.default_k
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"❓ PREGUNTA: {pregunta}")
            print(f"{'='*60}\n")
        
        # Retrieve
        if verbose:
            print(f"🔍 Buscando documentos relevantes (k={k})...")
        docs = self.retrieve_documents(pregunta, k=k)
        if verbose:
            print(f"✅ {len(docs)} documentos encontrados\n")
        
        # Generate
        if verbose:
            print(f"🤖 Generando respuesta...")
        result = self.generate_answer(pregunta, docs)
        
        # Agregar metadata
        result['query'] = pregunta
        result['num_docs_used'] = len(docs)
        result['retrieved_docs'] = docs
        
        if verbose:
            print(f"✅ Respuesta generada\n")
            print(f"💬 RESPUESTA:\n{result['answer']}\n")
        
        return result