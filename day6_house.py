from typing import Annotated, TypedDict

from operator import add as op_add

from langchain_community.tools import tool
 
class HouseState(TypedDict):

      plumbing: str

      electrical: str

      carpentry : str

      total_price : int

      steps_taken: Annotated[list, op_add]
def electrician_node(state: HouseState) -> dict:
    print("-> Done with the electrical work")
    return {
            "electrical": "done",
            "steps_taken": [15000]
    }
def carpenter_node(state: HouseState) -> dict:
    print("-> Done with the carpentry work")
    return {
            "carpentry": "done",
            "steps_taken": [20000]
    }
def plumber_node(state: HouseState) -> dict:
    print("-> Done with the plumbing work")
    return {
            "plumbing": "done",
            "steps_taken": [25000]
    }
def tool_node(state: HouseState) -> dict:
    print("-> computing the total bill")
    cost_list = state["steps_taken"]
    tot = add_numbers.invoke({"all_cost" :cost_list})
    return {          
            "total_price": tot
            }         
@tool
def add_numbers(all_cost: list[int]):
    """calculates the total amount"""
    total = 0
    for cost in all_cost:
        total += cost 
    return total    
from langgraph.graph import StateGraph
 
builder = StateGraph(HouseState)  
 
builder.add_node("electrician", electrician_node)
builder.add_node("carpenter", carpenter_node)
builder.add_node("plumber", plumber_node)
builder.add_node("calculator", tool_node)
from langgraph.graph import START, END
builder.add_edge(START, "electrician") 
builder.add_edge("electrician", "carpenter") 
builder.add_edge("carpenter", "plumber") 
builder.add_edge("plumber", "calculator") 
builder.add_edge("calculator", END)

 
app  = builder.compile()
initial_state ={"steps_taken": []}
from dotenv import load_dotenv
load_dotenv()
 
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()
 
langfuse_config = {"callbacks" : [langfuse_handler],
                   "metadata" :
                                {
                                    "langfuse_session_id": "langgraph_session",
                                    "langfuse_user_id" :"Nalla"
                                }
                    }
 
final_state = app.invoke(initial_state, config = langfuse_config)
 
print(final_state)
      