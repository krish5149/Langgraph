from typing import TypedDict
from langgraph.types import RetryPolicy
from langgraph.graph import StateGraph, START, END

class FaultTolerence(TypedDict):
    query: str
    result: str
    primary_failed: bool

def primary_node(state: FaultTolerence):
    try:
        print(" Trying Primary search........")
        if "weather" in state['query']:
            raise ValueError("Primary_Error")
        return {"result": f"Primary result for: {state['query']}", "primary_failed": False}
    except ValueError as e:
        print(f"  primary search failed: {e}")
        return {"primary_failed": True}
    
def backup_node(state: FaultTolerence):
    print("  using backup search instead...")
    return {"result": f"Backup result for: {state['query']}"}

def route_after_primary(state: FaultTolerence) -> str:
    return "backup_search" if state["primary_failed"] else "done"

builder = StateGraph(FaultTolerence)
builder.add_node("primary_search", primary_node)
builder.add_node("backup_search", backup_node)
builder.add_edge(START, "primary_search")
builder.add_conditional_edges(
    "primary_search", route_after_primary, {"backup_search": "backup_search", "done": END}
)
builder.add_edge("backup_search", END)

graph = builder.compile()


if __name__ == "__main__":
    print("=== Query that works fine on primary ===")
    result = graph.invoke({"query": "best pizza toppings", "result": "", "primary_failed": False})
    print("Result:", result["result"])

    print("\n=== Query that fails on primary, falls back ===")
    result = graph.invoke({"query": "weather in Chennai", "result": "", "primary_failed": False})
    print("Result:", result["result"])