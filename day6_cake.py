from typing import Annotated, TypedDict
from operator import add as op_add
from langchain.tools import tool
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain.tools import tool
import asyncio
import sys
from pathlib import Path
 
from langchain.mcp import MCPAdapter
from pathlib import Path
import asyncio
import sqlite3
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()
 
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()
# server_path = Path("day7_cake_mcp_server.py")
SERVER_URL = "http://127.0.0.1:8000/mcp"
 
async def load_cake_tools():

    async with MCPAdapter(SERVER_URL) as adapter:

        tools = await adapter.list_tools()

        tool_dictionary = {}

        for tool in tools:

            tool_dictionary[tool.name] = tool    

        return tool_dictionary
 
mcp_tools = asyncio.run(load_cake_tools())
 

class AgentState(TypedDict):
      user: str
      desired_flavour: str
      flavours_in_stock : str
      order_flavour: str
      federated_response : int
      steps_taken: Annotated[list, op_add]
      order_decision: str
      order_status: str
# def fetch_user_pref_node(state: AgentState) -> dict:
#     tool_out = fetch_user_data.invoke({"user_name" :state["user"]})
#     print(f"response from sql tool: {tool_out}")
#     return {          
#             "desired_flavour": tool_out,
#             "steps_taken" : ["user_data_fetch"]
#             }         
async def fetch_user_pref_node(state: AgentState) -> dict:
        tool_out = await mcp_tools["fetch_user_data"].ainvoke({
          "user_name": state["user"]
        })
        return {          
            "desired_flavour": tool_out,
            "steps_taken" :["user_pref_fetch"]
            }      
 
 
# def fetch_inv_node(state: AgentState) -> dict:
#     tool_out = fetch_inventory_data.invoke({})
#     print(f"response from sql tool: {tool_out}")
#     return {          
#             "flavours_in_stock": tool_out,
#             "steps_taken" : ["inv_fetch"]
#             }     
async def fetch_inv_node(state: AgentState) -> dict:
        tool_out = await mcp_tools["fetch_inventory_data"].ainvoke({})
        return {          
            "flavours_in_stock": tool_out,
            "steps_taken" :["inv_fetch"]
            }   

def order_confirmation_router(state : AgentState):
    decision = state["order_decision"]
    if decision == "yes":
        print("user accepted to make the order")
        return "place_order"
    return "end"
 
def place_order_node(state: AgentState):

    result = insert_order.invoke({
        "user_name": state["user"],
        "flavour": state["order_flavour"]
    })

    print(result)

    return {
        "order_status": result,
        "steps_taken": ["order inserted into database"]
    }

@tool
def insert_order(user_name: str, flavour: str) -> str:
    """Insert a customer's confirmed cake order into the orders table."""

    conn = sqlite3.connect("cake.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT Name, Price, Stock
            FROM inventory
            WHERE LOWER(Name) = LOWER(?)
            """,
            (flavour.strip(),)
        )

        item = cursor.fetchone()

        if item is None:
            return f"Order failed: {flavour} is not available in inventory."

        cake_name, price, stock = item

        if stock <= 0:
            return f"Order failed: {cake_name} is out of stock."

        cursor.execute(
            """
            INSERT INTO orders (user, flavour, price)
            VALUES (?, ?, ?)
            """,
            (user_name, cake_name, price)
        )

        conn.commit()

        return (
            f"Order successfully placed for {user_name}. "
            f"Cake: {cake_name}, Price: Rs. {price}"
        )

    except sqlite3.Error as e:
        conn.rollback()
        return f"Database error: {str(e)}"

    finally:
        conn.close()   
        
 
preference_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
inventory_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
federated_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
 
preference_llm_with_tools = preference_llm.bind_tools(
    [mcp_tools["fetch_user_data"]]
)
 
inventory_llm_with_tools = inventory_llm.bind_tools(
    [mcp_tools["fetch_inventory_data"]]
)

def preference_llm_node(state: AgentState):    
    messages_to_send = [
            {
                "role": "system",
                "content": """
                           You are the Preference LLM.
 
                            You have received the result from the preference database tool.
 
                            Analyze the tool result and determine the user's preferred
                            cake flavour.
 
                            Do not call the tool again.
 
                            If there is valid preference information, respond with
                            the preferred flavour and relevant information.
 
                            If no preference information was found, clearly say so.
                            """
            },
            {
                "role": "user",
                "content": f"""Find the cake flavour preference for user:{state["user"]}"""
            }
        ]
    response = preference_llm_with_tools.invoke(
        messages_to_send
    )
 
    if response.tool_calls:
        print("\nPreference LLM requested tool:")
        print(response.tool_calls)
        return {
             "steps_taken": [response]
        }
    return {
        "steps_taken": [response],
        "desired_flavour": response.content
    }

def inventory_llm_node(state: AgentState):    
    messages_to_send = [
            {
                "role": "system",
                "content": """
                           You are the inventory LLM.
 
                            You can access the fetch_inventory database tool.
 
                            Do not call the tool again.
 
 
                            """
            },
            {
                "role": "user",
                "content": f"""Check the inventory of the items"""
            }
        ]
    response = inventory_llm_with_tools.invoke(
        messages_to_send
    )
    if response.tool_calls:
        print("\ninventory llm requested tool:")
        print(response.tool_calls)
        return {
             "steps_taken": [response]
        }
    return {
        "steps_taken": [response],
        "flavours_in_stock": response.content
    }
def federated_llm_node(state: AgentState):

    messages_to_send = [
        {
            "role": "system",
            "content": """
            You are the cake ordering recommendation agent.

            Use the customer's previous order and available inventory
            to recommend one cake flavour.

            Choose a flavour that exists in the inventory.

            Return your answer in this format:

            Recommended flavour: <exact inventory flavour name>
            Reason: <short explanation>
            """
        },
        {
            "role": "user",
            "content": f"""
            User: {state['user']}
            Previous preference: {state['desired_flavour']}
            Available inventory: {state['flavours_in_stock']}
            """
        }
    ]

    response = federated_llm.invoke(messages_to_send)
    response_text = response.content[0]["text"]

    recommended_flavour = ""

    for line in response_text.splitlines():
        if line.lower().startswith("recommended flavour:"):
            recommended_flavour = line.split(":", 1)[1].strip()
            break

    return {
        "steps_taken": [response],
        "federated_response": response_text,
        "order_flavour": recommended_flavour
    }
def preference_router(state: AgentState):
    last_message = state["steps_taken"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "pref_tool"
    desired_flavour = state.get("desired_flavour", "")
    if desired_flavour:
        print("falvour is already available. So fetch the inventory")
        return "inv_llm"
    return  "end"
def inventory_router(state: AgentState):
    last_message = state["steps_taken"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "inv_tool"
    stock_flavour = state.get("flavours_in_stock", "")
    if stock_flavour:
        print("stock is already available. So move to next")
        return "fed_llm"
    return  "end"
from langgraph.types import interrupt, Command
 
def order_confirmation_node(state: AgentState):
    print("waiting for approval")             
    decision = interrupt({
        "message": "Do you want to go ahead with the order?",
        "recommendation":state["federated_response"],
        "options":["yes", "no"]
    })   
 
    print(f"\nuser response is {decision} ")    
    return {
        "order_decision" : str(decision).strip().lower(),
        "steps_taken" :["human decision"]
    }   
builder = StateGraph(AgentState)  
 
builder.add_node("pref_llm_node", preference_llm_node)
builder.add_node("inv_llm_node", inventory_llm_node)
builder.add_node("pref_tool_node", fetch_user_pref_node)
builder.add_node("inv_tool_node", fetch_inv_node)
builder.add_node("fed_llm_node", federated_llm_node)
builder.add_node("order_confirmation", order_confirmation_node)
builder.add_node("place_order", place_order_node)

from langgraph.graph import START, END
builder.add_edge(START, "pref_llm_node") 
# builder.add_edge("pref_llm_node", "inv_llm_node")
builder.add_conditional_edges(
    "pref_llm_node",
    preference_router,
    {
        "pref_tool": "pref_tool_node",
        "inv_llm": "inv_llm_node",
        "end" : END 
    }
)
builder.add_edge("pref_tool_node", "inv_llm_node") 
# builder.add_edge("inv_llm_node", "inv_tool_node") 
builder.add_conditional_edges(
    "inv_llm_node",
    inventory_router,
    {
        "inv_tool": "inv_tool_node",
        "fed_llm": "fed_llm_node",
        "end" : END 
    }
)
builder.add_edge("inv_tool_node", "fed_llm_node") 
builder.add_edge( "fed_llm_node", END) 
# builder.add_conditional_edges(
#     "order_confirmation",
#     order_confirmation_router,
#     {
#         "place_order": "place_order",
#         "end" : END 
#     }
# )
builder.add_edge("place_order", END)

from langgraph.checkpoint.memory import InMemorySaver
 
checkpoint = InMemorySaver()
app  = builder.compile(checkpointer=checkpoint)

initial_state ={"user":"nickith", "steps_taken": []}

# final_state = app.invoke(initial_state)

 
from IPython.display import Image, display
png_data = app.get_graph().draw_mermaid_png()
 
with open("langgraph_flow.png", "wb") as f:
    f.write(png_data)

langfuse_config = {"callbacks" : [langfuse_handler],
                   "configurable" : {
                       "thread_id": "cake_order_001"
                   },
                   "metadata" :
                                {
                                    "langfuse_session_id": "langgraph_session",
                                    "langfuse_user_id" :"manojkannas"
                                }
                    }
 
# final_state = app.invoke(initial_state, config = langfuse_config)
# print(final_state)
# if  "__interrupt__" in final_state:
#     # print("..>.." * 50)
#     # print("interrupt detected")
#     interrupt_data = final_state["__interrupt__"][0].value
#     print("..>.." * 15)
#     # print(interrupt_data)
#     print("Recommendation",interrupt_data["recommendation"] )
#     print("Options:",interrupt_data["options"])
 
#     human_response = input("Do you want to place the order?") 
#     print(f"User response : {human_response}")
#     final_state = app.invoke(Command(resume=human_response), config = langfuse_config)
#     print(final_state)
async def place_order_graph(name: str): 
    # final_state = await app.ainvoke(initial_state, config=langfuse_config) 
    # print(final_state)
    # return final_state["federated_response"]
    async for chunk in app.astream(
            {"user": name, "steps_taken": []},
            config=langfuse_config,
            stream_mode="updates"
        ):
            yield chunk
if __name__ == "__main__":
    asyncio.run(place_order_graph("nickith"))