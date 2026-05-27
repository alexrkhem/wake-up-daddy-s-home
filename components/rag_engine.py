"""
RAG Engine — LangChain + ChromaDB + Anthropic
Upload PDF textbooks, query them via Jarvis.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHROMA_DIR, ANTHROPIC_API_KEY

def load_and_index_pdf(pdf_path: str, collection_name: str) -> bool:
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        loader   = PyPDFLoader(pdf_path)
        docs     = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks   = splitter.split_documents(docs)

        client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
        embed_fn   = DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(collection_name, embedding_function=embed_fn)

        texts  = [c.page_content for c in chunks]
        ids    = [f"{collection_name}_{i}" for i in range(len(chunks))]
        metas  = [{"source": Path(pdf_path).name, "page": c.metadata.get("page", 0)} for c in chunks]

        batch = 100
        for i in range(0, len(texts), batch):
            collection.add(documents=texts[i:i+batch], ids=ids[i:i+batch], metadatas=metas[i:i+batch])
        return True
    except Exception as e:
        print(f"RAG index error: {e}")
        return False

def query_textbooks(question: str, collection_name: str, n_results: int = 5) -> str:
    try:
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
        embed_fn   = DefaultEmbeddingFunction()
        collection = client.get_collection(collection_name, embedding_function=embed_fn)
        results    = collection.query(query_texts=[question], n_results=n_results)

        if not results["documents"] or not results["documents"][0]:
            return ""
        context_parts = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            src = meta.get("source", "")
            pg  = meta.get("page", "?")
            context_parts.append(f"[{src} p.{pg}]\n{doc}")
        return "\n\n---\n\n".join(context_parts)
    except Exception:
        return ""

def list_collections() -> list:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return [c.name for c in client.list_collections()]
    except Exception:
        return []

def generate_practice_problems(topic: str, course_name: str, context: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "Set ANTHROPIC_API_KEY to generate problems."
    try:
        import anthropic
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt  = f"""You are tutoring a student in {course_name}.
Topic: {topic}

Textbook context:
{context[:3000] if context else 'No textbook context loaded.'}

Generate 3 practice problems of increasing difficulty. Include full worked solutions.
Use LaTeX-style notation for math (wrap in $ signs). Be thorough and pedagogical."""
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text
    except Exception as e:
        return f"Error: {e}"
