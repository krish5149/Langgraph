from typing import TypedDict, Annotated
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages

class StateManagement(TypedDict):
    messages: Annotated[list,add_messages]
    name: str

def node_a(state: StateManagement):
    return {
        "messages": f"Hi, {state['name']}"
    }

def node_b(state: StateManagement):
    return {
        "messages": f"Bad Welcome"
    }


graph = StateGraph(StateManagement)

graph.add_node("NodeA",node_a)
graph.add_node("NodeB",node_b)

graph.add_edge(START,"NodeA")
graph.add_edge("NodeA","NodeB")
graph.add_edge("NodeB",END)

graph_builder = graph.compile()

result = graph_builder.invoke({"name":"Ramki","messages":[]})
print(result)

graph_builder.get_graph().print_ascii()