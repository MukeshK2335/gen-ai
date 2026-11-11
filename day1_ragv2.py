from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
# from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

def chunk_markdown(markdown_text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["### ", "## ", "# ", "\n\n", "\n", " ", ""],
    )
    return text_splitter.split_text(markdown_text)
REPORT_PATH = "binance_hack.md"
with open(REPORT_PATH, "r", encoding="utf-8") as f:
    markdown_doc = f.read()
chunks = chunk_markdown(markdown_doc)
# for i, chunk in enumerate(chunks):
#     print(f"...>>>>... chunk num{i} has length {len(chunk)}")
#     print(chunk[:100])
 
def embed_and_store(
    chunks: list[str],
    source: str = "binance_hack.md",
    persist_dir: str = "./chroma_db",
    collection_name: str = "binance_incident",
):
    print("...entering the conversion.....")
    metadata_rows = []
    for i, chunk in enumerate(chunks):
        heading_lines = [line.strip() for line in chunk.splitlines() if line.strip().startswith('#') ]
        title = heading_lines[0] if heading_lines else "Untitled"
 
        metadata_rows.append({
            "title": title,
            "chunk_index": str(i),
            "chunk_length": str(len(chunk))
        })
    # embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # chunk_embeddings = embeddings_model.embed_documents(chunks)  
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
    print(".....converted the chunks to embedding...")
 
    return vector_store
 
embed_and_store(chunks)




def query_chroma_db(

    query: str,

    collection_name: str = "binance_incident",

    persist_dir: str = "./chroma_db",

    n_results: int = 3

):

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
 
    vector_store = Chroma(

            collection_name=collection_name,

            embedding_function=embeddings,

            persist_directory=persist_dir

        )  
 
    retriever = vector_store.as_retriever(

        search_type ="similarity",

        search_kwargs ={

            "k": n_results

        }

    )   

    retrieved_documents = retriever.invoke(query)

    return retrieved_documents
 
search_results = query_chroma_db("How does the hack occurred and what are the main causes of the hack?")

print(search_results)
 
 