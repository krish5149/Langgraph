from typing import Annotated, TypedDict
from dotenv import load_dotenv
import operator
from langgraph.checkpoint.memory import InMemorySaver
from langchain_groq import ChatGroq
from langgraph.graph import START, END, StateGraph, MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, AnyMessage

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile")

class MemoryManagement(TypedDict):
    messages: Annotated[list[AnyMessage],operator.add]
    llm_calls: int

def chat_bot(state: MemoryManagement):
    print("Agent is responding....")
    response = llm.invoke(
        [
            SystemMessage(
                content = """
                        you are a helpful ai assistant.
                        Use conversaation memory properly.
                        and answer based on previous messages 
                    """
            )
        ]
        +state["messages"]
    )

    return {
        "messages": [response],
        "llm_calls": state.get("llm_call",0)+1
    }

graph = StateGraph(MemoryManagement)
graph.add_node("Chat",chat_bot)
graph.add_edge(START,"Chat")
graph.add_edge("Chat",END)

memory = InMemorySaver()
app = graph.compile(checkpointer = memory)
config = {
    "configurable":{
        "thread_id":"user_1"
    }
}

result = app.invoke(
    {
        "messages":[HumanMessage(content="my name is Bahubali")],
        "llm_calls":0
    },
    config=config  # type: ignore
)

print("\nAI Message1:")
print(result["messages"][-1].content)

result = app.invoke(
    {
        "messages":[HumanMessage(content="what is my name")],
        "llm_calls":0
    },
    config=config # type: ignore
)

print("\nAI Message2:")
print(result["messages"][-1].content)
