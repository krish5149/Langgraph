from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

class State(TypedDict):
    number: int

def double(state: State):
    print("Node Started......")
    interrupt("Node is paused....")
    print("Node execution is completed....")
    return {
        "number":state["number"]*2
    }

graph = StateGraph(State)

graph.add_node("Double", double)
graph.add_edge(START,"Double")
graph.add_edge("Double",END)

checkpointer = MemorySaver()
graph_builder = graph.compile(checkpointer)

config = {
    "configurable": {
        "thread_id":"test_1"
    }
}

result = graph_builder.invoke({
    "number": 5,
},
config=config) #type:ignore

print("After Call 1:",result)

result2 = graph_builder.invoke(Command(resume="yes"), config=config) #type:ignore
print("After call 2:", result2)