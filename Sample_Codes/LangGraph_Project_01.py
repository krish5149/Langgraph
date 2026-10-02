from typing_extensions import Annotated, TypedDict
from dotenv import load_dotenv
import operator
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile")


class TravelAgent(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


cities_branch_1 = ["New York", "London", "Tokyo", "Paris", "Sydney", "Mumbai"]
cities_branch_2 = ["Dubai", "Berlin", "Singapore", "Toronto", "Bangkok", "Chennai"]

hotel_recommendations = {
    "New York": ["The Plaza Hotel", "Four Seasons New York"],
    "London": ["The Ritz London", "Savoy Hotel"],
    "Tokyo": ["Park Hyatt Tokyo", "Mandarin Oriental Tokyo"],
    "Paris": ["Hotel Ritz Paris", "Le Meurice"],
    "Sydney": ["Shangri-La Sydney", "Park Hyatt Sydney"],
    "Mumbai": ["Taj Mahal Palace", "The Oberoi Mumbai"],
    "Dubai": ["Burj Al Arab", "Atlantis The Palm"],
    "Berlin": ["Hotel Adlon Kempinski", "The Ritz-Carlton Berlin"],
    "Singapore": ["Marina Bay Sands", "Raffles Singapore"],
    "Toronto": ["Fairmont Royal York", "Shangri-La Toronto"],
    "Bangkok": ["Mandarin Oriental Bangkok", "The Peninsula Bangkok"],
    "Chennai": ["ITC Grand Chola", "Taj Coromandel"]
}

places_recommendations = {
    "New York": ["Statue of Liberty", "Central Park", "Times Square", "Metropolitan Museum of Art"],
    "London": ["Buckingham Palace", "Tower of London", "Big Ben", "British Museum"],
    "Tokyo": ["Shinjuku Gyoen", "Tokyo Tower", "Meiji Shrine", "Tsukiji Market"],
    "Paris": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Montmartre"],
    "Sydney": ["Sydney Opera House", "Harbour Bridge", "Bondi Beach", "Taronga Zoo"],
    "Mumbai": ["Gateway of India", "Marine Drive", "Elephanta Caves", "Chhatrapati Shivaji Maharaj Terminus"],
    "Dubai": ["Burj Khalifa", "Dubai Mall", "Palm Jumeirah", "Dubai Creek"],
    "Berlin": ["Brandenburg Gate", "Berlin Wall Memorial", "Museum Island", "Reichstag Building"],
    "Singapore": ["Marina Bay Sands", "Gardens by the Bay", "Sentosa Island", "Singapore Zoo"],
    "Toronto": ["CN Tower", "Royal Ontario Museum", "Distillery District", "Toronto Islands"],
    "Bangkok": ["Grand Palace", "Wat Arun", "Chatuchak Market", "Floating Markets"],
    "Chennai": ["Marina Beach", "Kapaleeshwarar Temple", "Fort St. George", "San Thome Basilica"]
}


@tool
def get_weather_tool(city: str) -> str:
    """Gets the weather information for the given city."""
    if city in cities_branch_1:
        return f"Weather in {city}: sunny. The city is known for its vibrant atmosphere."
    elif city in cities_branch_2:
        return f"Weather in {city}: winter. The city has a crisp and festive atmosphere."
    else:
        return f"We currently do not have a branch in {city}. Available cities are: {cities_branch_1 + cities_branch_2}"


@tool
def find_hotels_tool(city: str) -> list:
    """Returns the best hotels in the given city."""
    return hotel_recommendations.get(city, [])


@tool
def places_tool(city: str) -> list:
    """Returns the best places to visit in the given city."""
    return places_recommendations.get(city, [])


tools = [get_weather_tool, find_hotels_tool, places_tool]

llm_tools = llm.bind_tools(tools)


def assistant_node(state: TravelAgent):
    system_message = SystemMessage(
        content=(
            "You are a professional travel assistant. "
            "When the user mentions a city or plans a stay, use the tools to get weather, hotels, "
            "and places to visit. Then provide a clear travel recommendation."
        )
    )

    messages = [system_message] + state["messages"]

    response = llm_tools.invoke(messages)

    # Important: return the original response.
    # Do not create AIMessage(content=response.content), because that removes tool_calls.
    return {
        "messages": [response]
    }


graph = StateGraph(TravelAgent)

tool_node = ToolNode(tools)

graph.add_node("Assistant", assistant_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "Assistant")

graph.add_conditional_edges(
    "Assistant",
    tools_condition,
    {
        "tools": "tools",
        END: END
    }
)

# Important: after tool execution, go back to Assistant
graph.add_edge("tools", "Assistant")

app = graph.compile()

result = app.invoke({
    "messages": [HumanMessage(content="Planning to stay in London. Suggest hotels and places to visit.")]
})

print(result["messages"][-1].content)

app.get_graph().print_ascii()
