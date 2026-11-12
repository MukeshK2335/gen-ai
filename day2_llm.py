from dotenv import load_dotenv
from langchain_classic.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.langchain import CallbackHandler
from langchain.messages import HumanMessage,AIMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.runnables import RunnableLambda
 
load_dotenv()
key = "AQ.Ab8R.."
langfuse_handler = CallbackHandler()
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.3,
    timeout=15,
    max_tokens=1500,
    max_retries=3
)
class CustomResponse(BaseModel):
    msg: str = Field(description="The short answer")
    reference: str | None = None
# conversation = [
#     SystemMessage("You are software security expert who provide precise answers"),
#     HumanMessage("What is binance?"),
#     AIMessage("Binance is a popular bitcoin exchange company"),
#     HumanMessage("Was it hacked recently?")
# ]
context_binance  = ""
 
with open("binance_hack.md", "r") as fi:
    all_lines = fi.readlines()
    for this_line in all_lines:
        context_binance += this_line + "\n"
 
conversaton_template = ChatPromptTemplate([
    ("system", "You are an assistant to answer with the provided context: {context}"),
    ("human","{question}")
])
llm_with_structure = llm.with_structured_output(CustomResponse)
def validate(resp: CustomResponse) -> CustomResponse:
    if not resp.reference:
        return CustomResponse(msg =  "sorry. no reference", reference=None)
    return resp
chain =  conversaton_template | llm_with_structure | RunnableLambda(validate)
dict_input = {  "context":context_binance,    "question":"What is price of nvidia stock?" }    
 
# conversation = conversaton_template.format_messages(
#     context=context_binance,
#     question="Was binance hackeed recently?"
# )
# response = llm.invoke("what is the current cyber attack in Tamil Nadu government?",
#                       config={"callbacks": [langfuse_handler],
#                       "metadata":
#                       {
#                           "langfuse_session_id": "tamilnadu_cyber_1",
#                           "langfuse_user_id": "Mueksh"
#                       }
#                       })
response = chain.invoke(dict_input,
                      config={"callbacks": [langfuse_handler],
                      "metadata":
                      {
                          "langfuse_session_id": "tamilnadu_cyber_1",
                          "langfuse_user_id": "Mueksh"
                      }
                      })
 
print(response)