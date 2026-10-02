from typing import Annotated, TypedDict, Literal
import random
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt, Command, Send, RetryPolicy
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool

JOB_REQUIREMENTS = ["python", "sql", "aws"]

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key="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")  # type:ignore


def merge_dicts(exisiting: dict, new: dict):
    print(f"[merge_dicts] existing={exisiting}, new={new}")
    return {**exisiting, **new}


class State(TypedDict):
    application_text: str
    years_experience: int
    skills: list[str]
    education_level: str
    messages: Annotated[list, add_messages]
    skill_match_score: float
    background_results: Annotated[dict, merge_dicts]
    overall_score: float
    decision: str
    recruiter_notes: str


class ApplicationInfo(BaseModel):
    years_of_experience: int
    skills: list[str]
    education_level: str


def parse_application(state: State):
    print("\n[parse_application] STARTING")
    print(f"[parse_application] input text: {state['application_text']!r}")
    structured_llm = llm.with_structured_output(ApplicationInfo)
    response = structured_llm.invoke(state["application_text"])
    print(f"[parse_application] parsed -> years={response.years_of_experience}, "       # type:ignore
          f"skills={response.skills}, education={response.education_level}")            # type:ignore
    return {
        "years_experience": response.years_of_experience,       # type:ignore
        "skills": response.skills,                              # type:ignore
        "education_level": response.education_level             # type:ignore
    }


@tool
def check_skill_match(skill: str):
    "Check if a given skill is one of the job's required skills"
    print(f"[TOOL check_skill_match] checking skill={skill!r}")
    if skill.lower() in JOB_REQUIREMENTS:
        print(f"[TOOL check_skill_match] result: required skill")
        return "required skill"
    print(f"[TOOL check_skill_match] result: skill not required")
    return "skill not required"


@tool
def estimate_salary_expectation(years_experience: int):
    """Estimate a reasonable salary range based on years of experience."""
    print(f"[TOOL estimate_salary_expectation] years={years_experience}")
    base = 4000 + years_experience * 5000
    result = f"The estimated salary is between {base} + {base+10000}"
    print(f"[TOOL estimate_salary_expectation] result: {result}")
    return result


skill_tools = [check_skill_match, estimate_salary_expectation]
llm_with_tools = llm.bind_tools(skill_tools)


def skill_match_agent(state: State) -> dict:
    print("\n[skill_match_agent] STARTING")
    print(f"[skill_match_agent] messages so far: {len(state['messages'])}")
    system = SystemMessage(content=(
        f"Candidate skills: {state['skills']}. Job requires: {JOB_REQUIREMENTS}. "
        "Use check_skill_match on each candidate skill to see how many are "
        "required skills. Once done, give a final answer ending with a new "
        "line 'SCORE: <0-100>' reflecting how well the candidate matches."
    ))

    message = state["messages"] or [HumanMessage(content="Evaluate this candidate's skill match.")]
    response = llm_with_tools.invoke([system] + message)

    if response.tool_calls:                                                                                     # type:ignore
        print(f"[skill_match_agent] model requested {len(response.tool_calls)} tool call(s): "                  # type:ignore
              f"{[tc['name'] for tc in response.tool_calls]}")                                                  # type:ignore
    else:
        print(f"[skill_match_agent] model gave final answer: {response.content!r}")

    return {
        "messages": [response]
    }


def extract_skill_score(state: State) -> dict:
    print("\n[extract_skill_score] STARTING")
    text = state["messages"][-1].content
    print(f"[extract_skill_score] reading final message: {text!r}")
    score = 50.0
    if "SCORE:" in text:
        try:
            score = float(text.rsplit("SCORE:", 1)[1].strip())
        except ValueError:
            print("[extract_skill_score] WARNING: found 'SCORE:' but couldn't parse a number")
    print(f"[extract_skill_score] final score={score}")
    return {"skill_match_score": score}


def background_check(state: State):
    print("\n[background_check] DISPATCHING parallel checks")
    print(f"[background_check] years_experience={state['years_experience']}, "
          f"application_text={state['application_text'][:40]!r}...")
    return [
        Send("check_work_history", {"years_of_experience": state["years_experience"]}),
        Send("check_red_flags", {"application_text": state["application_text"]})
    ]


def check_work_history(branch_state: dict) -> dict:
    print(f"\n[check_work_history] STARTING with input={branch_state}")
    if random.random() < 0.2:
        print("[check_work_history] SIMULATED FAILURE — will trigger RetryPolicy")
        raise ConnectionError("work history verification service blip")

    years = branch_state["years_of_experience"]
    score = 100 if years >= 2 else 70
    print(f"[check_work_history] score={score}")
    return {"background_results": {"work_history_score": score}}


def check_red_flags(branch_state: dict) -> dict:
    print(f"\n[check_red_flags] STARTING with input keys={list(branch_state.keys())}")
    if random.random() < 0.2:
        print("[check_red_flags] SIMULATED FAILURE — will trigger RetryPolicy")
        raise ConnectionError("red flag scan service blip")
    text = branch_state["application_text"].lower()
    score = 70 if "gap" in text or "unexplained" in text else 100
    print(f"[check_red_flags] score={score}")
    return {"background_results": {"red_flags_score": score}}


def background_done(state: State) -> dict:
    print("\n[background_done] STARTING")
    results = state["background_results"]
    print(f"[background_done] merged results so far: {results}")
    work = results.get("work_history_score", 100)
    flags = results.get("red_flags_score", 100)
    weighted = work * 0.4 + flags * 0.6
    print(f"[background_done] overall_background_score={weighted}")
    return {"background_results": {**results, "overall_background_score": weighted}}


def combine_scores(state: State) -> dict:
    print("\n[combine_scores] STARTING")
    bg_score = state["background_results"].get("overall_background_score", 100)
    print(f"[combine_scores] skill_match_score={state['skill_match_score']}, "
          f"background_score={bg_score}")
    overall = state["skill_match_score"] * 0.5 + bg_score * 0.5
    print(f"[combine_scores] overall_score={overall}")
    return {"overall_score": overall}


def auto_accept(state: State) -> dict:
    print("\n[auto_accept] STARTING — score qualified for auto-accept")
    return {"decision": "accepted", "recruiter_notes": "Auto-accepted, strong overall score."}


def auto_reject(state: State) -> dict:
    print("\n[auto_reject] STARTING — score qualified for auto-reject")
    return {"decision": "rejected", "recruiter_notes": "Auto-rejected, low overall score."}


def route_by_score(state: State) -> Literal["auto_accept", "auto_reject", "recruiter_review"]:
    score = state["overall_score"]
    print(f"\n[route_by_score] evaluating score={score}")
    if score >= 75:
        print("[route_by_score] -> auto_accept")
        return "auto_accept"
    elif score <= 40:
        print("[route_by_score] -> auto_reject")
        return "auto_reject"
    else:
        print("[route_by_score] -> recruiter_review (borderline)")
        return "recruiter_review"


def recruiter_review(state: State):
    print("\n[recruiter_review] STARTING — pausing for human input")
    decision = interrupt(
        f"Borderline candidate — overall score {state['overall_score']:.1f}. Accept? yes/no"
    )
    print(f"[recruiter_review] human responded: {decision!r}")
    if decision.lower() == "yes":
        print("[recruiter_review] -> accepted")
        return Command(
            update={
                "decision": "accepted", "recruiter_notes": "Approved by recruiter."
            }
        )
    else:
        print("[recruiter_review] -> rejected")
        return Command(
            update={
                "decision": "rejected", "recruiter_notes": "Rejected by recruiter."
            }
        )


graph = StateGraph(State)
graph.add_node("parse_application", parse_application)
graph.add_node("skill_match_agent", skill_match_agent)
graph.add_node(
    "check_work_history", check_work_history, retry_policy=RetryPolicy(max_attempts=3)      # type:ignore
)
graph.add_node(
    "check_red_flags", check_red_flags, retry_policy=RetryPolicy(max_attempts=3)            # type:ignore
)
graph.add_node("background_done", background_done)
graph.add_node("Order_Tool", ToolNode(skill_tools))
graph.add_node("extract_skill_score", extract_skill_score)
graph.add_node("combine_scores", combine_scores)
graph.add_node("auto_accept", auto_accept)
graph.add_node("recruiter_review", recruiter_review)
graph.add_node("auto_reject", auto_reject)

graph.add_edge(START, "parse_application")
graph.add_edge("parse_application", "skill_match_agent")
graph.add_conditional_edges(
    "skill_match_agent",
    tools_condition, {
        "tools": "Order_Tool",
        END: "extract_skill_score"
    })
graph.add_edge("Order_Tool", "skill_match_agent")
graph.add_conditional_edges(
    "extract_skill_score",
    background_check,
    ["check_work_history", "check_red_flags"]
)
graph.add_edge("check_work_history", "background_done")
graph.add_edge("check_red_flags", "background_done")
graph.add_edge("background_done", "combine_scores")
graph.add_conditional_edges(
    "combine_scores",
    route_by_score, {
        "auto_accept": "auto_accept",
        "recruiter_review": "recruiter_review",
        "auto_reject": "auto_reject"
    }
)
graph.add_edge("auto_accept", END)
graph.add_edge("recruiter_review", END)
graph.add_edge("auto_reject", END)

app = graph.compile(checkpointer=MemorySaver())

config = {
    "configurable": {
        "thread_id": "order1"
    },
    "recursion_limit": 50
}


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "candidate_1"}, "recursion_limit": 50}

    inputs = {
        "application_text": (
            "5 years of experience in software engineering. Skilled in Python, "
            "SQL, and Docker. Bachelor's degree in Computer Science. "
            "No employment gaps."
        ),
        "years_experience": 0,
        "skills": [],
        "education_level": "",
        "messages": [],
        "skill_match_score": 0.0,
        "background_results": {},
        "overall_score": 0.0,
        "decision": "",
        "recruiter_notes": "",
    }

    result = app.invoke(inputs, config=config)                                                  # type:ignore

    if "__interrupt__" in result:
        print("\n(paused for recruiter decision)")
        result = app.invoke(Command(resume="yes"), config=config)                               # type:ignore

    print("\nFinal decision:", result["decision"])
    print("Notes:", result["recruiter_notes"])