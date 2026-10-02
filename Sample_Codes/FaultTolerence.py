from typing import TypedDict
import random
from langgraph.types import RetryPolicy
from langgraph.graph import StateGraph, START, END

class FaultTolerenceRetry(TypedDict):
    attempt: int
    result: str

def retry_node(state: FaultTolerenceRetry):
    attempt_number = state["attempt"] + 1
    v = random.random()
    print(v)

    if v < 0.9:
        raise ConnectionError("Simulated network failure")

    return {"attempt": attempt_number, "result": "success!"}

graph = StateGraph(FaultTolerenceRetry)

graph.add_node("Retry",
               retry_node,
               retry_policy=RetryPolicy(max_attempts=4)
            )

graph.add_edge(START, "Retry")
graph.add_edge("Retry", END)

app = graph.compile()

if __name__ == "__main__":
    try:
        result = app.invoke({"attempt": 0, "result": ""})
        print("Final result:", result)
    except ConnectionError as e:
        print("Gave up after all retries:", e)