from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Annotated
from dotenv import load_dotenv
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

# =========== Creating tools =================

@tool
def add(a: int, b: int) -> int:
    """Adding two numbers"""
    c = a + b
    return c

@tool
def multiply(a: int, b: int) -> int:
    """Multiplying two number"""
    c = a * b
    return c

@tool
def weather(city: str) -> str:
    """Return the city's weather"""
    return f"The weather of the {city} is 25`0 Sunny..."

tools = [add, multiply, weather]

# =========== Binding tools =================

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile")
llm_with_tools = llm.bind_tools(tools)
test = HumanMessage(content="What is 20 add 20")
# response = llm_with_tools.invoke([test])
# print(response.tool_calls)
# print(response.content)


# =========== Building Graph =================

tool_node = ToolNode(tools)


def agent_node(state: MessagesState):
    
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

graph = StateGraph(MessagesState)
graph.add_node("Agent", agent_node)
graph.add_node("Tools", tool_node)

graph.add_edge(START, "Agent")
graph.add_conditional_edges(
    "Agent",
    tools_condition,
    {
        "tools": "Tools",
        END: END
    }
)

app = graph.compile()

result = app.invoke({
    "messages": [HumanMessage(content="What is 25 multiplied by 48?")]
})

print(result)

app.get_graph().print_ascii()