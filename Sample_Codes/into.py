from typing import TypedDict
from langgraph.graph import START, END, StateGraph

class WelcomeMessage(TypedDict):
    message: str
    result: str

def greet_node(state: WelcomeMessage):
    name = state["message"]
    return {
        "result": f"Hi! {name}, Welcome back!"
    }


# 1. Create the graph with your state
graph_builder = StateGraph(WelcomeMessage)

# 2. Add nodes
graph_builder.add_node("greeter", greet_node)

# 3. Add edges (define the flow)
graph_builder.add_edge(START, "greeter")
graph_builder.add_edge("greeter", END)

# 4. Compile
graph = graph_builder.compile()

result = graph.invoke({"message": "Alice", "result": ""})
print(result)

# This works without internet
graph.get_graph().print_ascii()