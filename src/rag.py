import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

class RAGManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_fn = embedding_functions.VoyageEmbeddingFunction(
            api_key=os.getenv("VOYAGE_API_KEY"),
            model_name="voyage-code-3"
        )
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_fn
        )

    def _get_splitter(self, doc_name: str):
        ext = os.path.splitext(doc_name)[1].lower()# always 2 no matter how many dots

        language_map = {
            
            ".py": Language.PYTHON,
            
            ".js": Language.JS,
            ".jsx": Language.JS,
            ".ts": Language.TS,
            ".tsx": Language.TS,
            
            ".c": Language.CPP,
            ".cpp": Language.CPP,
            ".cc": Language.CPP,
            ".cxx": Language.CPP,
            ".h": Language.CPP,
            ".hpp": Language.CPP,
           
            ".java": Language.JAVA,
           
            ".cs": Language.CSHARP,
            
            ".html": Language.HTML,
            ".htm": Language.HTML,
        }

        if ext in language_map:
            return RecursiveCharacterTextSplitter.from_language(
                language=language_map[ext],
                chunk_size=1000,
                chunk_overlap=150
            )

        # Fallback for .txt, .md, and unrecognized file types
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )

    def ingest_document(self, text: str, doc_name: str):
        splitter = self._get_splitter(doc_name)
        chunks = splitter.split_text(text)
        
        ids = [f"{doc_name}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": doc_name} for _ in chunks]

        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

    def query(self, user_query: str, n_results: int = 3) -> str:
        results = self.collection.query(
            query_texts=[user_query],
            n_results=n_results
        )
        documents = results.get("documents", [[]])[0]
        return "\n---\n".join(documents) if documents else "No relevant context found."