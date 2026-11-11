from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma
 
class StoreManager:
    def embed_and_store(
        self,
        chunks: list[str],
        source: str = "tamil_nadu_government_cybersecurity_incident_report.md",
        persist_dir: str = "./chroma_db",
        collection_name: str = "tamil_nadu_cybersecurity_incident"):
            metadata_rows = []
            documents = []
            for i, chunk in enumerate(chunks):
                heading_lines = [line.strip() for line in chunk.splitlines() if line.strip().startswith('#') ]
                title = heading_lines[0] if heading_lines else "Untitled"
 
                metadata_rows.append({
                    "title": title,
                    "chunk_index": str(i),
                    "chunk_length": str(len(chunk))
                })
                documents.append(
                    Document(
                        page_content=chunk
                    )
                )
 
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=persist_dir
            )  
            vector_store.reset_collection()
 
            vector_store.add_texts(
                texts=chunks,
                metadatas=metadata_rows,
                ids=[f"chunk_{i}" for i in range(len(chunks))]
            )
            return documents, vector_store