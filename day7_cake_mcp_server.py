import sqlite3
from fastmcp import FastMCP
 
mcp = FastMCP("Cake Database Server")

@mcp.tool
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

@mcp.tool
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
if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000
    )