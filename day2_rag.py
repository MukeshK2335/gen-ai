from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
 
# from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from ChunkManager import ChunkManager
from StorageManager import StoreManager
from RetrieveManager import RetrieveManager
 
load_dotenv()
 
REPORT_PATH = "tamil_nadu_government_cybersecurity_incident_report.md"
 
with open(REPORT_PATH, "r", encoding="utf-8") as f:
    markdown_doc = f.read()
 
chunkMan = ChunkManager()
chunks = chunkMan.chunk_markdown(markdown_doc)
storeMan = StoreManager()
 
for i, chunk in enumerate(chunks):
    print(f"...>>>>... chunk num{i} has length {len(chunk)}")
    print(chunk[:100])
 
documents, vector_store = storeMan.embed_and_store(chunks)
# search_results = query_chroma_db("How much money is lost due to the hack?")
search_query = "How much money was reportedly stolen in the Tamil Nadu Government cyberattack?"
 
retrieveMan  = RetrieveManager()
results = retrieveMan.query_hybrid(search_query, documents=documents, vector_store=vector_store, n_results = 3)
 
final_results = retrieveMan.rerank_documents("How much money is lost due to the hack?", results)
 
print(final_results)
 
# for i, res in enumerate(results):
#     print(f"\n*** Result {i} ***")
#     print(f"Content:\n{res.page_content}")