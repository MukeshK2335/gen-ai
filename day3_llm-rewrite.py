from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.langchain import CallbackHandler
from langchain.messages import HumanMessage,AIMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from RedactManager import RedactManager
from ChunkManager import ChunkManager
from StorageManager import StoreManager
from RetrieveManager import RetrieveManager
from config import load_config
from prompts import get_prmpt

 
load_dotenv()
prompt_det = get_prmpt("binance_qa",2)
config = load_config()
chunkman = ChunkManager(config)
storeMan = StoreManager(config)
retrievalMan = RetrieveManager(config)

langfuse_handler = CallbackHandler()
context_binance  = ""
 
with open("binance_hack.md", "r") as fi:
    all_lines = fi.readlines()
    for this_line in all_lines:
        context_binance += this_line + "\n"

def debug_step(data):
    print("...inspecting...")
    return data

redact = RedactManager()
redacted_context = redact.performingRedactionOfPII(context_binance)
chunk = chunkman.chunk_markdown(redacted_context)
documents, vector_store = storeMan.embed_and_store(chunk)
question = "How much was lost in binance hack?"

llm = ChatGoogleGenerativeAI(model = "gemini-3.1-flash-lite", temperature=0)
# Query Rewriting
rewrite_instruction = """
You rewrite the question into concise, keyword search-friendly text.
Preserve the original meaning.
Return only the rewritten question.
"""

rewrite_template = ChatPromptTemplate.from_messages(
    [
        ("system", rewrite_instruction),
        ("human", "{quest}")
    ]
)

rewrite_chain = rewrite_template | llm

rewrite_content = rewrite_chain.invoke({"quest": question}).content[0]["text"]


search_result = retrievalMan.query_hybrid(
    rewrite_content, documents, vector_store
)

final_result = retrievalMan.rerank_documents(
    rewrite_content, search_result
)
#old
# search_result = retrievalMan.query_hybrid(question,documents,vector_store)
# final_result = retrievalMan.rerank_documents(question,search_result)

#prompt = ChatPromptTemplate.from_template("Answer the question:\"{question}\", based on the context: {ctxt}")
prompt = ChatPromptTemplate.from_template(prompt_det["system"])


parser = StrOutputParser()

uppercase_converter = RunnableLambda(lambda text : text.upper())

chain  = prompt | debug_step | llm | debug_step | parser | debug_step | uppercase_converter |debug_step
# response = chain.invoke({
#             "question": question,
#             "ctxt":final_result
#                 },        config={"callbacks": [langfuse_handler],
#                             "metadata" :
#                               {
#                                   "langfuse_session_id": "binance_session_N",
#                                   "langfuse_user_id" :"MANOJKANNA S",
#                                   "prompt_name": prompt_det["name"],
#                                   "prompt_version": prompt_det["version"],
#                               }})
response = chain.invoke({
    "question": rewrite_content,
    "ctxt": final_result
}, config={
    "callbacks": [langfuse_handler],
    "metadata": {
        "langfuse_session_id": "binance_session_N",
        "langfuse_user_id": "MANOJKANNA S",
        "prompt_name": prompt_det["name"],
        "prompt_version": prompt_det["version"],
    }
})
print(response)