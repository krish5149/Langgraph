from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt, Command, Send
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from operator import add
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

IN_STOCK = {"pepperoni": True, "mushroom": True, "pineapple": True}
LARGE_PIZZA = {"pepperoni": True, "mushroom": True}

llm = ChatGroq(model="llama-3.3-70b-versatile",api_key="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") #type:ignore

class PizzaOrderBot(TypedDict):
    order_text: str        
    messages: Annotated[list, add_messages]   
    checks: Annotated[list, add]     
    price: float
    approved: bool
    status: str
    no_of_pizza: int

class PizzaInfo(BaseModel):
    no_of_pizza: int

@tool
def topping_availability(topping: str):
    """Check if a topping is available; return True if available, else False."""
    if IN_STOCK.get(topping.lower()):
        return "in_stock"
    return "not_in_stock"

llm_with_tools = llm.bind_tools([topping_availability])

def order_taker(state: PizzaOrderBot):
    system = SystemMessage(content=(
        "You take pizza orders. Use the check_topping tool for any topping "
        "mentioned in the order. Once checked, reply with a short confirmation."
    ))

    message = HumanMessage(content=state["order_text"])
    response = llm_with_tools.invoke([system]+[message])
    return {
        "messages": [response]
    }

def count_no_of_pizzas(state: PizzaOrderBot):
    structured_llm = llm.with_structured_output(PizzaInfo)
    result = structured_llm.invoke(state["order_text"])
    return {
        "no_of_pizza" : result.no_of_pizza  #type:ignore
    }

def checking_price(state: PizzaOrderBot):
    if "large" in state["order_text"].lower():
        return {"price": 15.99 * state["no_of_pizza"]}
    return {"price": 10.99 * state["no_of_pizza"]}

def dispatch_check(state: PizzaOrderBot):
    return [
        Send("run_check",{"check":"kitchen_busy"}),
        Send("run_check",{"check":"delevery distance"})
    ]

def run_check(branch_state: dict):
    if branch_state["check"].lower() == "kitchen_busy":
        result = "Kitchen is moderately busy, ~20 min wait."
    else:
        result = "Delivery address is within normal range."

    return {
        "checks":[result]
    }

def checks_done(state: PizzaOrderBot):
    return{}

def ask_manager(state: PizzaOrderBot):
    decision = interrupt(f"Order totals ${state['price']}. Manager approve? yes/no")
    if decision == "yes":
        return {
            "approved" : True
        }

def router_by_price(state: PizzaOrderBot):
    if state["price"] > 30.0:
        return "ask_manager"
    else:
        return "finalize_order"
    
def finalize_order(state: PizzaOrderBot):
    return {"status": "Order confirmed and sent to kitchen."}

graph = StateGraph(PizzaOrderBot)

graph.add_node("Assistant",order_taker)
graph.add_node("Count",count_no_of_pizzas)
graph.add_node("order_tool",ToolNode([topping_availability]))
graph.add_node("Price",checking_price)
graph.add_node("run_check",run_check) #type:ignore
graph.add_node("checks_done",checks_done)
graph.add_node("Ask_manager",ask_manager)
graph.add_node("finalize_order",finalize_order)

graph.add_edge(START,"Assistant")
graph.add_conditional_edges(
    "Assistant",
    tools_condition,{
        "tools": "order_tool",
        END: "Count"
    }
)
graph.add_edge("order_tool","Assistant")
graph.add_edge("Count","Price")
graph.add_conditional_edges(
    "Price",
    dispatch_check,
    ["run_check"]
)
graph.add_conditional_edges(
    "checks_done",
    router_by_price,{
        "ask_manager": "Ask_manager",
        "finalize_order": "finalize_order"
    }
)
graph.add_edge("Ask_manager","finalize_order")
graph.add_edge("finalize_order",END)
graph.add_edge("run_check","checks_done")

app = graph.compile(checkpointer=MemorySaver())

config = {
    "configurable":{
        "thread_id": "order1"
    }
}


if __name__ == "__main__":
    result = app.invoke(
        {"order_text": "large pepperoni 2 pizzas", "messages": [],
             "checks": [], "price": 0.0, "approved": False, "status": "","no_of_pizza":0},
            config=config       #type:ignore
        )
    
    if "__interrupt__" in result:
        print("paused......")
        result = app.invoke(Command(resume="yes"), config=config)   #type:ignore

    print("\nFinal status:", result["status"])


