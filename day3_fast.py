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
    name: str = Field(min_length=4)
    # quest: str = Field(min_length=25)


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


from day6_cake import place_order_graph
 
@app.post("/order")

async def request_order(user: User):

    try:

        answer = await place_order_graph(user.name)

        return {"answer": answer}

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


from fastapi.responses import StreamingResponse

import json

@app.post("/order/stream")

async def place_order_stream(user: User):

    async def event_generator():

        try:

            async for node_update in place_order_graph(user.name):

                yield f"data: {json.dumps(node_update, default=str)}\n\n"

            yield "event: done\ndata: {}\n\n"

        except Exception as e:

            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
 
    return StreamingResponse(

        event_generator(),

        media_type="text/event-stream",

        headers={

            "Cache-Control": "no-cache",

            "Connection": "keep-alive",

            "X-Accel-Buffering": "no",

        },

    )

 
 