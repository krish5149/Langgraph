from typing import TypedDict
from langgraph.graph import START, END, StateGraph

class ConditionalEdges(TypedDict):
    number1: int
    operation1: str
    number2: int
    number3: int
    number4: int
    operation2: str
    finalNumber1: int
    finalNumber2: int

def decide_node(state: ConditionalEdges):
    if state['operation1'] == "+":
        return "Addition_Operation"

    return "Subtraction_Operation"

def add_node(state: ConditionalEdges):
    state['finalNumber1'] = state['number1'] - state['number2']
    return state

def subtract_node(state: ConditionalEdges):
    state['finalNumber1'] = state['number1'] + state['number2']
    return state

def add_node2(state: ConditionalEdges):
    state['finalNumber2'] = state['number3'] - state['number4']
    return state

def subtract_node2(state: ConditionalEdges):
    state['finalNumber2'] = state['number3'] + state['number4']
    return state

def decide_node2(state: ConditionalEdges):
    if state['operation2'] == "+":
        return "Addition_Operation2"

    return "Subtraction_Operation2"


graph = StateGraph(ConditionalEdges)

graph.add_node("Addition",add_node)
graph.add_node("Subtraction",subtract_node)
graph.add_node("Addition2",add_node2)
graph.add_node("Subtraction2",subtract_node2)
graph.add_node("route", lambda state:state)      # just passthrough function

# Conditional Edge
graph.add_conditional_edges(
    START,
    decide_node,
    {
        "Addition_Operation": "Addition",
        "Subtraction_Operation": "Subtraction"
    }
)

graph.add_edge("Addition","route")
graph.add_edge("Subtraction","route")

graph.add_conditional_edges(
    "route",
    decide_node2,
    {
        "Addition_Operation2": "Addition2",
        "Subtraction_Operation2": "Subtraction2"
    }
)

graph.add_edge("Addition2",END)
graph.add_edge("Subtraction2",END)



graph_builder = graph.compile()

result = graph_builder.invoke({"number1":10,"operation1":"-","number2":20,"number3":30,"number4":40,"operation2":"+","finalNumber1":0,"finalNumber2":0})
print(result)


graph_builder.get_graph().print_ascii()
    