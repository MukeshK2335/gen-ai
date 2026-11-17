from typing import Annotated, TypedDict
from operator import add as op_add
from langchain.tools import tool
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
import sqlite3

class AgentState(TypedDict):
      user: str
      desired_flavour: str
      flavour_in_stock: str
      federated_response : int
      steps_taken: Annotated[list, op_add]

def fetch_user_pref_node(state: AgentState) -> dict:
    tool_out = fetch_user_data.invoke({"user_name" : state["user"]})
    print(f"response from sql tool: {tool_out}")
    return {          
      "desired_flavour": tool_out,
      "steps_taken":["user_pref_fetched"]
            }         
 
 
def fetch_inv_node(state: AgentState) -> dict:
    tool_out = fetch_inventory_data.invoke({})
    print(f"response from sql tool: {tool_out}")
    return {          
            "flavour_in_stock": tool_out,
            "steps_taken":["inventory_fetched"]
            }
         

@tool
def fetch_user_data(user_name: str) -> str:
    """Fetches a user's past orders of cake flavour and order value."""    
    conn = sqlite3.connect("cake.db")
    cursor = conn.cursor()    
    try:
        cursor.execute("SELECT user, flavour, price  FROM orders WHERE user = ?", (user_name,))
        rows = cursor.fetchall() 
        if rows:
            orderHistory = "\n".join([f"{itm[0]} ordered {itm[1]} for Rs. {itm[2]}"  for itm in rows])   
            return orderHistory
        return f"No user data found for ID: {user_name}"        
    except sqlite3.Error as e:
        return f"Database error encountered: {str(e)}"
    finally:
        conn.close() 


@tool

def fetch_inventory_data() -> str:

    """Fetches available flavour from the inventory table."""    

    conn = sqlite3.connect("cake.db")

    cursor = conn.cursor()    

    try:

        cursor.execute("SELECT Name, Price, Stock  FROM inventory")

        rows = cursor.fetchall() 

        if rows:

            inv_details = "\n".join([f"{itm[0]} costs {itm[1]} and available quantity is {itm[2]}"  for itm in rows])   

            return inv_details

        return f"No inventory data found"        

    except sqlite3.Error as e:

        return f"Database error encountered: {str(e)}"

    finally:

        conn.close()

 
preference_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
inventory_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
federated_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
 
preference_llm_with_tools = preference_llm.bind_tools(
    [fetch_user_data]
)
 
inventory_llm_with_tools = inventory_llm.bind_tools(
    [fetch_inventory_data]
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
                           You are the federated LLM who gets data from two other agents.
                            The results are available as   "desired_flavour",  " flavours_in_stock"
                            You can generate the appropriate response cake ordering for the user.
 
                            """
            },
            {
                "role": "user",
                "content": f"""user :  {state['user']} 
                        prefered falvour : {state['desired_flavour']}
                        stock details : {state['flavour_in_stock']}
                        provide thefinal recommendation
                        """
            }
        ]
    response = federated_llm.invoke(
        messages_to_send)
    return {
        "steps_taken": [response],
        "federated_response": response.content[0]["text"]
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
 

    
 
 
builder = StateGraph(AgentState)  
builder.add_node("pref_llm_node", preference_llm_node)
builder.add_node("inv_llm_node", inventory_llm_node)
builder.add_node("pref_tool_node",fetch_user_pref_node)
builder.add_node("inv_tool_node", fetch_inv_node)
builder.add_node("fed_llm_node", federated_llm_node)

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
#builder.add_edge("inv_llm_node", "inv_tool_node") 
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
builder.add_edge("fed_llm_node", END)

app  = builder.compile()
from IPython.display import Image, display
png_data = app.get_graph().draw_mermaid_png()
 
with open("langgraph_flow.png", "wb") as f:
    f.write(png_data)

initial_state ={"user": "nickith", "steps_taken": []}

# final_state = app.invoke(initial_state)
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