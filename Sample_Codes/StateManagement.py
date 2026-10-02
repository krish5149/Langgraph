from typing import TypedDict, Annotated
from langgraph.graph import START, END, StateGraph
import operator

class StateManagement(TypedDict):
    last_update: str
    log_message: Annotated[list, operator.add]

def node_a(state: StateManagement):
    return{
        "last_update": "from_node_a",
        "log_message": ["hai from a"]
    }

def node_b(state: StateManagement):
    return{
        "last_update": "from_node_b",
        "log_message": ["hai from b"]
    }

def node_c(state: StateManagement):
    return{
        "last_update": "from_node_c",
        "log_message": ["hai from c"]
    }

graph = StateGraph(StateManagement)

graph.add_node("node_a", node_a)
graph.add_node("node_b", node_b)
graph.add_node("node_c", node_c)


graph.add_edge(START, "node_a")
graph.add_edge("node_a", "node_b")
graph.add_edge("node_b", "node_c")
graph.add_edge("node_b", END)

graph_builder = graph.compile()

result = graph_builder.invoke({"last_update":" ","log_message":[]})
print(result)

graph_builder.get_graph().print_ascii()