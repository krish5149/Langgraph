from typing_extensions import Annotated, TypedDict
from dotenv import load_dotenv
import operator
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile")


class TravelAgent(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    budget: int

flight = {
    "Indigo": 450,
    "Air India": 500,
    "Airbus": 650
}

def flight_tool(source: str,destination: str,state: TravelAgent):
    """ Return flight with price"""
    if state["budget"] < flight["Airbus"]:
        state["budget"] = state["budget"] - flight["Airbus"]
    elif state["budget"] < flight["Air India"]:
        state["budget"] = state["budget"] - flight["Air India"]
    else:
        state["budget"] = state["budget"] - flight["Indigo"]

    return state





