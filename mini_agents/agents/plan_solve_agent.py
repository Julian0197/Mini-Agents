"""Plan and Solve Agent"""

import ast
from typing import Optional, List, Dict
from ..core.agent import Agent
from ..core.llm import MiniAgentsLLM
from ..core.config import Config
from ..core.message import Message

DEFAULT_PLANNER_PROMPT = """
You are a top-tier AI planning expert. Your task is to decompose complex user problems into an action plan consisting of multiple simple steps.
Make sure each step in the plan is an independent, executable subtask, and strictly follow logical order.
Your output must be a Python list, where each element is a string describing a subtask(less than 4 subtasks at most).

Question: {question}

Output your plan strictly in the following format:
```python
["Step 1", "Step 2", "Step 3", ...]
```
"""

DEFAULT_EXECUTOR_PROMPT = """
You are a top-tier AI execution expert. Your task is to strictly follow the given plan and solve the problem step by step.
You will receive the original problem, the complete plan, and the steps completed so far with their results.
Please focus on solving the "current step" concisely and only output the final answer for that step, without any additional explanations or dialogue.

# Original Question:
{question}

# Complete Plan:
{plan}

# History and Results:
{history}

# Current Step:
{current_step}

Please only output the answer for the "current step":
"""

class Planner:
    """Planner - responsible for decomposing complex problems into simple steps"""
    def __init__(self, llm_client: MiniAgentsLLM, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_PLANNER_PROMPT

    def create_plan(self, question: str, **kwargs) -> List[str]:
        prompt = self.prompt_template.format(question=question, **kwargs)
        messages = [Message(content=prompt, role="system").to_dict()]

        print("--- Generating plan ---")
        chunks = []
        for chunk in self.llm_client.stream(messages, **kwargs):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        print()
        response_text = "".join(chunks) if chunks else ""
        print("✅ Plan generated.")

        try:
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except Exception as e:
            print(f"❌ Failed to parse plan: {e}")
            return []

class Executor:
    """Executor - responsible for executing the plan step by step"""
    def __init__(self, llm_client: MiniAgentsLLM, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_EXECUTOR_PROMPT

    def execute(self, question: str, plan: List[str], **kwargs) -> str:
        """
        Execute task according to plan

        Args:
            question: Original problem
            plan: Execution plan
            **kwargs: LLM call parameters

        Returns:
            Final answer
        """
        history = ""
        final_answer = ""

        print("\n--- Executing plan ---")
        for i, step in enumerate(plan, 1):
            print(f"\n🔄 Executing Step {i}/{len(plan)}: {step}")
            prompt = self.prompt_template.format(
                question=question,
                plan=plan,
                history=history,
                current_step=step,
                **kwargs
            )
            messages = [Message(content=prompt, role="system").to_dict()]
            step_chunks = []
            for chunk in self.llm_client.stream(messages, **kwargs):
                print(chunk, end="", flush=True)
                step_chunks.append(chunk)
            print()
            step_result = "".join(step_chunks) if step_chunks else ""
            print(f"✅ Result for Step {i}.")

            history += f"Step {i}: {step}\nResult: {step_result}\n\n"
            final_answer = step_result  # Update final answer to the latest step result
            print(f"✅ Step {i} completed, result: {final_answer}")

        return final_answer

class PlanAndSolveAgent(Agent):
    """
    Plan and Solve Agent - Decompose planning and step-by-step execution agent

    This agent can:
    1. Decompose complex problems into simple steps
    2. Execute step by step according to plan
    3. Maintain execution history and context
    4. Derive final answer

    Especially suitable for multi-step reasoning, math problems, and complex analysis tasks.
    """

    def __init__(
        self,
        name: str,
        llm_client: MiniAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        """
        Initialize PlanAndSolveAgent

        Args:
            name: Agent name
            llm: LLM instance
            system_prompt: System prompt
            config: Config object
            custom_prompts: Custom prompt templates {"planner": "", "executor": ""}
        """
        super().__init__(name, llm_client, system_prompt, config)

        # Set prompt templates: user custom takes priority, otherwise use default
        if custom_prompts:
            planner_prompt = custom_prompts.get("planner")
            executor_prompt = custom_prompts.get("executor")
        else:
            planner_prompt = None
            executor_prompt = None

        self.planner = Planner(llm_client, planner_prompt)
        self.executor = Executor(llm_client, executor_prompt)

    def run(self, input_text: str, **kwargs) -> str:
        """
        Run Plan and Solve Agent

        Args:
            input_text: Problem to solve
            **kwargs: Other parameters

        Returns:
            Final answer
        """
        print(f"\n🤖 {self.name} starting to process question: {input_text}")

        # 1. Generate plan
        plan = self.planner.create_plan(input_text, **kwargs)
        if not plan:
            final_answer = "Failed to generate valid action plan, task terminated."
            print(f"\n--- Task terminated ---\n{final_answer}")

            # Save to history
            self.add_to_history(Message(content=input_text, role="user"))
            self.add_to_history(Message(content=final_answer, role="assistant"))

            return final_answer

        # 2. Execute plan
        final_answer = self.executor.execute(input_text, plan, **kwargs)
        print(f"\n--- 🔚Task completed ---\nFinal answer: {final_answer}")

        # Save to history
        self.add_to_history(Message(content=input_text, role="user"))
        self.add_to_history(Message(content=final_answer, role="assistant"))

        return final_answer
