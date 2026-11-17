from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from day3_llm_rag import ask_question
from day3_llm_rag_copy import ChatManager

app = FastAPI()

@app.get("/hello/{name}")
def say_hello(name: str):
    if len(name) < 4:
        raise HTTPException(
            status_code=400,
            detail="Name must be at least 4 characters"
        )
    return {"msg" : f"Hello {name}"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
#uvicorn hello_fast:app

"""@app.get("/hello/{name}")
def say_hello(name: str):
    return {"msg" : f"Hello {name}"}"""

class User(BaseModel):
    nam: str = Field(min_length=4)
    quest: str = Field(min_length=25)


def get_chat_manager() -> ChatManager:
    return ChatManager()    
 
@app.post("/ask")
def create_greeting(user: User, chatMan : ChatManager = Depends(get_chat_manager)):
    try:
        answer = chatMan.ask_question(user.quest)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )