# LangGraph Projects

A collection of small Python examples exploring agent workflows with [LangGraph](https://github.com/langchain-ai/langgraph) and LangChain. The examples cover pizza ordering, résumé screening, and an unfinished travel-planning prototype.

## Projects

| File | Description |
| --- | --- |
| `PizzaOrderBot.py` | Takes a pizza order, checks topping availability, estimates the price, runs mock kitchen and delivery checks, and pauses for manager approval when the total is over $30. Its example run resumes the approval interrupt with a “yes” response. |
| `ResumeSkillClassifier.py` | Parses résumé text into structured fields, evaluates skills against Python, SQL, and AWS requirements, runs simulated background checks, combines scores, and accepts, rejects, or pauses for recruiter review. Background-check failures are simulated and retried. |
| `AI_Travel_Planner_Pro.py` | An incomplete travel-planning prototype. It currently defines a travel-agent state and a basic flight-price dictionary/function; it does not yet build or run a LangGraph workflow. |

The pizza and résumé workflows use in-memory LangGraph checkpointing, so their state is not persisted between program runs.

## Requirements

- Python 3.10 or later
- A Groq API key for the pizza and résumé examples
- Python packages: `langgraph`, `langchain-core`, `langchain-groq`, `langchain-google-genai`, `python-dotenv`, `pydantic`, and `typing-extensions`

Install the packages in a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install langgraph langchain-core langchain-groq langchain-google-genai python-dotenv pydantic typing-extensions
```

## Running the examples

Run each script from the project directory:

```powershell
python PizzaOrderBot.py
python ResumeSkillClassifier.py
```

The pizza example submits a sample order for two large pepperoni pizzas. The résumé example evaluates a sample candidate. Both scripts call the Groq-hosted `llama-3.3-70b-versatile` model.

## API key safety

The pizza and résumé scripts currently pass a Groq API key directly to `ChatGroq`. **Do not publish or reuse that key. Rotate it if it was ever shared, and replace the hard-coded credential with an environment-variable-based configuration before running or sharing these scripts.** The travel prototype calls `load_dotenv()`, but it does not yet use an LLM or read a key.

## Notes

- Topping availability, delivery distance, kitchen wait time, and résumé background checks are local example logic; they do not contact real services.
- The résumé scoring and hiring outcomes are illustrative and should not be used as the sole basis for real employment decisions.
- `AI_Travel_Planner_Pro.py` is a prototype rather than a runnable planner.
