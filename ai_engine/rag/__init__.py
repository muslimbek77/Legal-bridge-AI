"""
RAG (Retrieval-Augmented Generation) Module.
Uses vector search to find relevant laws and generate context-aware responses.
Supports both Ollama (local) and OpenAI (cloud) LLMs.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)




class LegalRAG:
    """
    RAG system for legal document retrieval and generation.
    Uses ChromaDB for vector storage and LLM for generation.
    Supports Ollama (local) and OpenAI (cloud) as LLM backends.
    """
    
    def __init__(
        self,
        vector_store_path: str = "./vector_store",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        llm_model: str = "llama3.1",
        llm_base_url: str = "http://localhost:11434",
        use_openai: bool = False,
        openai_model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize RAG system.
        
        Args:
            vector_store_path: Path to ChromaDB storage
            embedding_model: Sentence transformer model for embeddings
            llm_model: LLM model name (for Ollama)
            llm_base_url: Ollama server URL
            use_openai: Force using OpenAI instead of Ollama
            openai_model: OpenAI model to use
        """
        self.vector_store_path = Path(vector_store_path)
        self.embedding_model_name = embedding_model
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url
        self.use_openai = use_openai
        self.openai_model = openai_model
        
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.llm_client = None
        self.openai_client = None
        self.llm_type = None  # 'ollama', 'openai', or None
        
        self._initialized = False
    
    def initialize(self):
        """Initialize all components."""
        if self._initialized:
            return
        
        try:
            # Initialize embeddings
            from sentence_transformers import SentenceTransformer
            self.embeddings = SentenceTransformer(self.embedding_model_name)
            
            # Initialize ChromaDB
            import chromadb
            from chromadb.config import Settings
            
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_store_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="legal_documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Initialize LLM - try Ollama first, then OpenAI
            self._initialize_llm()
            
            self._initialized = True
            logger.info(f"RAG system initialized successfully with LLM: {self.llm_type}")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize LLM backend - Ollama or OpenAI."""
        
        # If force OpenAI, skip Ollama
        if not self.use_openai:
            # Try Ollama first
            try:
                import ollama
                self.llm_client = ollama.Client(host=self.llm_base_url)
                # Test connection
                self.llm_client.list()
                self.llm_type = 'ollama'
                logger.info(f"Ollama initialized at {self.llm_base_url}")
                return
            except Exception as e:
                logger.warning(f"Could not initialize Ollama: {e}")
                self.llm_client = None
        
        # Try OpenAI as fallback
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_api_key)
                self.llm_type = 'openai'
                logger.info("OpenAI initialized as LLM backend")
                return
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI: {e}")
                self.openai_client = None
        
        # No LLM available
        self.llm_type = None
        logger.warning("No LLM backend available (neither Ollama nor OpenAI)")
    
    def add_documents(self, documents: List[Dict]) -> int:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with 'text', 'metadata', 'id' keys
            
        Returns:
            Number of documents added
        """
        if not self._initialized:
            self.initialize()
        
        texts = [doc['text'] for doc in documents]
        ids = [doc.get('id', str(i)) for i, doc in enumerate(documents)]
        metadatas = [doc.get('metadata', {}) for doc in documents]
        
        # Generate embeddings
        embeddings = self.embeddings.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(documents)
    
    def search(self, query: str, n_results: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of matching documents with scores
        """
        if not self._initialized:
            self.initialize()
        
        # Generate query embedding
        query_embedding = self.embeddings.encode([query]).tolist()[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )
        
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else None,
            })
        
        return formatted
    
    def search_laws(self, query: str, contract_type: str = None, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant laws.
        
        Args:
            query: Search query
            contract_type: Filter by contract type
            n_results: Number of results
            
        Returns:
            Relevant law articles
        """
        filter_dict = None
        if contract_type:
            filter_dict = {"contract_type": contract_type}
        
        return self.search(query, n_results, filter_dict)
    
    def generate_response(
        self,
        query: str,
        context_docs: List[Dict],
        system_prompt: str = None
    ) -> str:
        """
        Generate a response using LLM with retrieved context.
        
        Args:
            query: User query
            context_docs: Retrieved documents for context
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        if not self._initialized:
            self.initialize()
        
        if not self.llm_type:
            return "LLM client not available (neither Ollama nor OpenAI configured)"
        
        # Build context from documents
        context_lines = []
        for doc in context_docs:
            law_name = doc.get('metadata', {}).get('law_name') or "Noma'lum"
            article_number = doc.get('metadata', {}).get('article_number', '')
            text = doc['text']
            context_lines.append(
                f"Qonun: {law_name}\n"
                f"Modda: {article_number}\n"
                f"Matn: {text}"
            )
        context = "\n\n".join(context_lines)
        
        # Default system prompt
        if not system_prompt:
            system_prompt = """Siz O'zbekiston Respublikasi qonunchiligi bo'yicha ekspert yuridik yordamchisiz.
Javobni quyidagi talablarga qat'iy rioya qilgan holda bering:
- Faqat kontekstdagi qonun moddalariga tayangan holda xulosa qiling
- Aniq, lo'nda va amaliy tavsiyalar bering
- Noma'lum bo'lsa: "Aniq ma'lumot yetarli emas" deb yozing
- Tuzilishi: 1) Moslik 2) Xavflar 3) Tavsiya 4) Zarur o'zgartirish matni"""
        
        # Build prompt
        full_prompt = f"""KONTEKST (Tegishli qonun moddalari):
{context}

SAVOL: {query}

JAVOB:"""
        
        try:
            if self.llm_type == 'ollama':
                # Use Ollama
                response = self.llm_client.chat(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_prompt}
                    ],
                    options={
                        "temperature": 0.1,
                        "num_predict": 1024,
                    }
                )
                return response['message']['content']
            
            elif self.llm_type == 'openai':
                # Use OpenAI
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1024,
                )
                return response.choices[0].message.content
            
            else:
                return "LLM backend not configured"
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Xatolik: {str(e)}"
    
    def analyze_clause(self, clause_text: str, contract_type: str = None) -> Dict:
        """
        Analyze a contract clause against relevant laws.
        
        Args:
            clause_text: The clause text to analyze
            contract_type: Type of contract
            
        Returns:
            Analysis result with relevant laws and issues
        """
        # Search for relevant laws
        relevant_laws = self.search_laws(clause_text, contract_type)
        
        # Generate analysis
        analysis_prompt = f"""Quyidagi shartnoma bandini O'zbekiston qonunchiligi nuqtai nazaridan tahlil qiling.

    BAND:
    {clause_text}

    Talab qilinadigan chiqish:
    1) Moslik: qisqa baho (mos/mos emas) va izoh
    2) Xavflar: 2-4 punkt, aniq ifoda
    3) Tavsiya: 1-3 aniq tavsiya
    4) O'zgartirish matni: zarur bo'lsa, taklif etilgan band matni"""
        
        analysis = self.generate_response(analysis_prompt, relevant_laws)
        
        return {
            'clause': clause_text,
            'relevant_laws': relevant_laws,
            'analysis': analysis,
        }

    def analyze_clause_structured(self, clause_text: str, contract_type: str = None) -> Dict:
        """Analyze clause and return structured JSON dict with graceful fallback.

        Returns keys: compliance (str), risks (list[str]), recommendations (list[str]), rewrite (str)
        """
        # Retrieve relevant laws as context
        relevant_laws = self.search_laws(clause_text, contract_type)

        # Strict JSON-only instruction
        system_prompt = (
            "Siz O'zbekiston qonunchiligi bo'yicha ekspert yuridik yordamchisiz. "
            "Faqat JSON qaytaring; matnli izohlar, prefix/suffix kerak emas."
        )

        json_schema_hint = (
            "Qaytaring faqat quyidagi JSON formatda (boshqa hech narsa qo'shmang):\n"
            "{\n"
            "  \"compliance\": \"mos|mos emas|noaniq\",\n"
            "  \"risks\": [\"...\"],\n"
            "  \"recommendations\": [\"...\"],\n"
            "  \"rewrite\": \"...\"\n"
            "}"
        )

        prompt = (
            f"Quyidagi bandni tahlil qiling va qat'iy JSON qaytaring.\n\n"
            f"BAND:\n{clause_text}\n\n"
            f"Talablar:\n"
            f"- compliance: 'mos', 'mos emas' yoki 'noaniq'\n"
            f"- risks: 2-4 aniq punkt\n"
            f"- recommendations: 1-3 amaliy tavsiya\n"
            f"- rewrite: kerak bo'lsa, taklif etilgan band matni\n\n"
            f"{json_schema_hint}"
        )

        # Build context and call LLM
        try:
            if not self._initialized:
                self.initialize()
            if not self.llm_type:
                raise RuntimeError("LLM backend not configured")

            # Build context lines like in generate_response
            context_lines = []
            for doc in relevant_laws:
                law_name = doc.get('metadata', {}).get('law_name') or "Noma'lum"
                article_number = doc.get('metadata', {}).get('article_number', '')
                text = doc['text']
                context_lines.append(
                    f"Qonun: {law_name}\nModda: {article_number}\nMatn: {text}"
                )
            context = "\n\n".join(context_lines)

            user_content = f"KONTEKST:\n{context}\n\n{prompt}"

            if self.llm_type == 'ollama':
                response = self.llm_client.chat(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    options={"temperature": 0.1, "num_predict": 768},
                )
                content = response['message']['content']
            else:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.1,
                    max_tokens=768,
                )
                content = response.choices[0].message.content

            import json
            try:
                data = json.loads(content)
                # Minimal validation and coercion
                result = {
                    'compliance': str(data.get('compliance', 'noaniq')),
                    'risks': list(data.get('risks', []))[:6],
                    'recommendations': list(data.get('recommendations', []))[:6],
                    'rewrite': str(data.get('rewrite', '')),
                }
            except Exception:
                # Fallback: return raw content mapped into rewrite, minimal fields
                result = {
                    'compliance': 'noaniq',
                    'risks': [],
                    'recommendations': [],
                    'rewrite': content.strip(),
                }

            return {
                'clause': clause_text,
                'relevant_laws': relevant_laws,
                'analysis_structured': result,
            }
        except Exception as e:
            logger.error(f"Structured clause analysis failed: {e}")
            return {
                'clause': clause_text,
                'relevant_laws': relevant_laws,
                'error': str(e),
            }
    
    def get_law_reference(self, law_name: str, article_number: str) -> Optional[Dict]:
        """
        Get specific law article by reference.
        
        Args:
            law_name: Name of the law
            article_number: Article number
            
        Returns:
            Law article if found
        """
        results = self.search(
            f"{law_name} {article_number}-modda",
            n_results=1,
            filter_dict={
                "law_name": law_name,
                "article_number": article_number
            }
        )
        
        return results[0] if results else None


class LegalDocumentLoader:
    """
    Utility class for loading legal documents into RAG system.
    """
    
    @staticmethod
    def load_law_from_json(json_path: str) -> List[Dict]:
        """
        Load law from JSON file.
        
        Expected format:
        {
            "law_name": "...",
            "short_name": "...",
            "articles": [
                {"number": "1", "title": "...", "content": "..."},
                ...
            ]
        }
        """
        import json
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        law_name = data.get('law_name', '')
        short_name = data.get('short_name', '')
        
        for article in data.get('articles', []):
            doc = {
                'id': f"{short_name}_{article['number']}",
                'text': article.get('content', ''),
                'metadata': {
                    'law_name': law_name,
                    'short_name': short_name,
                    'article_number': article.get('number', ''),
                    'article_title': article.get('title', ''),
                    'applies_to': article.get('applies_to', []),
                }
            }
            documents.append(doc)
        
        return documents
    
    @staticmethod
    def load_law_from_text(
        text: str,
        law_name: str,
        short_name: str = ""
    ) -> List[Dict]:
        """
        Parse law from plain text and create documents.
        Uses simple pattern matching for article boundaries.
        """
        import re
        
        # Pattern for article headers
        article_pattern = re.compile(
            r'(?:^|\n)\s*(\d+)\s*[-\.]\s*(?:modda|статья)[\.:]?\s*(.+?)(?=\n\s*\d+\s*[-\.]\s*(?:modda|статья)|$)',
            re.IGNORECASE | re.DOTALL
        )
        
        documents = []
        
        for match in article_pattern.finditer(text):
            number = match.group(1)
            content = match.group(2).strip()
            
            # Try to extract title (first line)
            lines = content.split('\n')
            title = lines[0] if lines else ""
            
            doc = {
                'id': f"{short_name}_{number}",
                'text': content,
                'metadata': {
                    'law_name': law_name,
                    'short_name': short_name,
                    'article_number': number,
                    'article_title': title,
                }
            }
            documents.append(doc)
        
        return documents
