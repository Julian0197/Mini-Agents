This project is inspired by and based on the [hello-agents](https://github.com/datawhalechina/hello-agents). It serves as a learning foundation and reference for development.

## Project Structure

```
Mini-Agents/
├── mini_agents/                  # Core package
│   ├── core/                     # Core
│   │   ├── agent.py              # Agent base class
│   │   ├── llm.py                # MiniAgentsLLM unified LLM interface (invoke/stream)
│   │   ├── message.py            # Message
│   │   ├── config.py             # Config
│   │   └── exceptions.py         # Exceptions
│   │
│   └── agents/                   # Agent implementations
│       ├── plan_solve_agent.py   # PlanAndSolveAgent
│       └── react_agent.py        # ReActAgent
│
├── examples/
│   └── plan_solve_agent.py      # Example usage
├── main.py
├── pyproject.toml
└── requirements.txt
```
