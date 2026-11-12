from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field
from day3_llm_rag import ask_question
 
app = FastAPI()
 
@app.get("/health")
def health_check():
    return {"status" : "ok"}

@app.get("/hello/{name}")
def say_hello(name: str):
    if len(name) < 4:
        raise HTTPException(
            status_code=400,
            detail="Name must be at least 4 characters"
        )
    return {"msg" : f"Hello {name}"}
class User(BaseModel):
    nam: str = Field(min_length=4)
    quest: str = Field(min_length=25)
 
@app.post("/hello")
def create_greeting(user: User):
    return {"msg" : f"Hello {user.nam}"}
# @app.post("/ask")
# def create_greeting(user: User):
#     return {"msg" : f"{user.name} asked: {user.quest}"}
@app.post("/ask")
def create_greeting(user: User):
    answer = ask_question(user.quest)
    return {"msg" : f"{user.nam} answer: {answer}"}
