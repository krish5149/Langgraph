from typing import TypedDict
from langgraph.graph import START, END, StateGraph
import random

class LoopingAgent(TypedDict):
    player_name: str
    guesses: list[int]
    attempts: int
    lower_bound: int
    upper_bound: int
    target_number: int
    hint: str

# --- Nodes ---

def greet_player_node(state: LoopingAgent):
    print(f"Welcome, {state['player_name']}! The game has begun.")
    print(f"I'm thinking of a number between {state['lower_bound']} and {state['upper_bound']}\n")
    
    # Generate the target number using state boundaries
    state['target_number'] = random.randint(state['lower_bound'], state['upper_bound'])
    state["attempts"] = 0
    return state

def guess_node(state: LoopingAgent):
    guessed_num = int(input(f"Attempt {state['attempts'] + 1}/7 - Enter your guess: "))
    state['guesses'].append(guessed_num)
    state["attempts"] += 1 
    return state

# --- Conditional Router (Decision Maker) ---

def decide_next_step(state: LoopingAgent):
    last_guess = state['guesses'][-1]
    
    # 1. Check win condition
    if last_guess == state['target_number']:
        print(f"\n🎉 GAME OVER: You found it! The number was {state['target_number']}.")
        return "End"
        
    # 2. Check lose condition
    if state["attempts"] >= 7:
        print(f"\n❌ GAME OVER: Out of attempts! The number was {state['target_number']}.")
        return "End"
    
    # 3. Check boundaries
    if last_guess < state['lower_bound'] or last_guess > state['upper_bound']:
        print(f"⚠️ Out of range! Please guess between {state['lower_bound']} and {state['upper_bound']}.\n")
        return "Loop"
        
    # 4. Give relative hints
    if last_guess < state['target_number']:
        print(f"📉 The number {last_guess} is too low. Try higher!\n")
    else:
        print(f"📈 The number {last_guess} is too high. Try lower!\n")
        
    return "Loop"


# --- Graph Construction ---

graph = StateGraph(LoopingAgent)

# Register only the two action nodes
graph.add_node("GreetingPlayer", greet_player_node)
graph.add_node("Guesser", guess_node)

# Core workflow progression
graph.add_edge(START, "GreetingPlayer")
graph.add_edge("GreetingPlayer", "Guesser")

# The looping conditional edge (using our routing function)
graph.add_conditional_edges(
     "Guesser",
     decide_next_step,
     {
        "Loop": "Guesser",  # Loops directly back to input prompt
        "End": END          # Exits the graph execution
     }
)

graph_builder = graph.compile()

# --- Run the Game ---

# Adjusted boundaries to match 1 to 20 game parameters
result = graph_builder.invoke({
    "player_name": "Jackson Durai",
    "guesses": [],
    "attempts": 0,
    "lower_bound": 1, 
    "upper_bound": 20,
    "hint": "",
    "target_number": 0
})

print("\n--- Text Graph Structure ---")
def print_terminal_graph():
    lines = [
        "      +---------------+ ",
        "      |   __start__   | ",
        "      +---------------+ ",
        "              |         ",
        "              v         ",
        "    +------------------+ ",
        "    |  GreetingPlayer  | ",
        "    +------------------+ ",
        "              |         ",
        "              v         ",
        "    +------------------+ ",
        "+-->|     Guesser      | ",
        "|   +------------------+ ",
        "|             |         ",
        "|             v         ",
        "|   +------------------+ ",
        "|   | decide_next_step | ",
        "|   +------------------+ ",
        "|      /            \\   ",
        "|  ['Loop']     ['End'] ",
        "|    /                \\ ",
        "+---+                  v ",
        "               +---------------+ ",
        "               |    __end__    | ",
        "               +---------------+ "
    ]
    
    print("\n" + "•" * 40)
    print("       LIVE TERMINAL GRAPH FLOW")
    print("•" * 40 + "\n")
    for line in lines:
        print(line)
    print("\n" + "•" * 40)

# Call this instead of print_ascii()
print_terminal_graph()