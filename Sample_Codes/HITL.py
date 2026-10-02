from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

class State(TypedDict):
    number: int

def double(state: State):
    print("Node Started......")
    answer = interrupt("Should i doble this number or not")
    print(f"Human said: {answer}")

    if answer == "yes":
        return {"number":state["number"]*2}
    else:
        return {"number":state['number']}

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

# ==============================================================================================================


from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Literal

class State2(TypedDict):
    number: int
    decision: str   # will hold "yes" or "no" after the human answers

# NODE 1: pauses, stores the human's raw answer in state
def ask_human(state: State2) -> dict:
    print("Node started: asking human...")
    answer = interrupt("Should I double this number? yes/no")
    return {"decision": answer}

# NODE 2: only runs if human said yes
def double_it(state: State2) -> dict:
    print("Doubling the number...")
    return {"number": state["number"] * 2}

# NODE 3: only runs if human said no
def leave_it(state: State) -> dict:
    print("Leaving the number unchanged...")
    return {"number": state["number"]}

# ROUTING FUNCTION: looks at state["decision"], picks the next node's name
def route_based_on_decision(state: State2) -> Literal["double_it", "leave_it"]:
    if state["decision"] == "yes":
        return "double_it"
    else:
        return "leave_it"

builder = StateGraph(State)
builder.add_node("ask_human", ask_human)
builder.add_node("double_it", double_it)
builder.add_node("leave_it", leave_it)

builder.add_edge(START, "ask_human")

# THIS is the new piece: after ask_human, branch to a DIFFERENT NODE
# (not just a different value) depending on the human's answer
builder.add_conditional_edges(
    "ask_human",
    route_based_on_decision,
    {"double_it": "double_it", "leave_it": "leave_it"},
)

builder.add_edge("double_it", END)
builder.add_edge("leave_it", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "test_3"}}

# Call 1 — pauses inside ask_human
result1 = graph.invoke({"number": 5, "decision": ""}, config=config)    #type:ignore
print("After call 1:", result1)

# Call 2 — human approves
result2 = graph.invoke(Command(resume="yes"), config=config)     #type:ignore
print("After call 2:", result2)