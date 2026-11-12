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

 
load_dotenv()
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
prompt = ChatPromptTemplate.from_template("Answer the question:\"{question}\", based on the context: {ctxt}")
convert_upper=RunnableLambda(lambda x: x.upper())
llm=ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",temperature=0)

parser=StrOutputParser()


chain=prompt|llm|debug_step|parser|debug_step|convert_upper
response=chain.invoke({"question":"What is binance?", "ctxt": redacted_context}, config={"callbacks": [langfuse_handler]})
print(response)