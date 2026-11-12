from dotenv import load_dotenv
from langchain_classic.prompts import ChatPromptTemplate
from langchain_classic.schema import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.langchain import CallbackHandler
from langchain.messages import HumanMessage,AIMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.runnables import RunnableLambda
from RedactManager import RedactManager
from ChunkManager import ChunkManager
from StorageManager import StoreManager
from RetrieveManager import RetrieveManager
 
load_dotenv()
 
chunkMan = ChunkManager()
storeMan = StoreManager()
retrieveMan = RetrieveManager()
def debug_step(data):

    print("...inspecting...")

    return data

context_binance = ""

with open("binance_hack.md", "r") as fi:
    all_lines = fi.readlines()
    for this_line in all_lines:
        context_binance += this_line + "\n"
redactMan = RedactManager()
redacted_context = redactMan.pii_filter(context_binance)
langfuse_handler = CallbackHandler()
chunks = chunkMan.chunk_markdown(redacted_context)
documents, vector_store = storeMan.embed_and_store(chunks)
question = "How much was lost in the binance hack?"
search_results = retrieveMan.query_hybrid(question, documents, vector_store)
final_result = retrieveMan.rerank_documents(question, search_results)
prompt = ChatPromptTemplate.from_template("Answer the question:\"{question}\", based on the context: {ctxt}")
convert_upper=RunnableLambda(lambda x: x.upper())
llm=ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",temperature=0)

parser=StrOutputParser()


chain=prompt|llm|debug_step|parser|debug_step|convert_upper
response=chain.invoke({"question": question, "ctxt": final_result}, config={"callbacks": [langfuse_handler]})
print(response)