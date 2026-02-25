"""Reflection Agent - An agent capable of self-reflection and iterative refinement"""

from typing import Optional, Dict, Any, List
from ..core.agent import Agent
from ..core.llm import MiniAgentsLLM
from ..core.config import Config
from ..core.message import Message

DEFAULT_PROMPTS = {
    "initial": """
Please complete the following task:

Task: {task}

Provide a complete and accurate answer.
""",
    "reflect": """
Please carefully review the following answer and identify potential issues or areas for improvement:

# Original Task:
{task}

# Current Answer:
{content}

Analyze the quality of this answer, point out any shortcomings, and provide specific suggestions for improvement.
If the answer is already satisfactory, reply with "No improvement needed".
""",
    "refine": """
Please improve your answer based on the feedback:

# Original Task:
{task}

# Previous Answer:
{last_attempt}

# Feedback:
{feedback}

Provide an improved answer.
""",
}


class Memory:
    """
    Simple short-term memory module for storing the agent's action and reflection trajectory.
    """

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """Add a new record to memory"""
        self.records.append({"type": record_type, "content": content})
        print(f"[Memory] Updated with a new '{record_type}' record.")

    def get_trajectory(self) -> str:
        """Format all memory records into a coherent text string"""
        trajectory = ""
        for record in self.records:
            if record["type"] == "execution":
                trajectory += (
                    f"--- Previous Attempt (Code) ---\n{record['content']}\n\n"
                )
            elif record["type"] == "reflection":
                trajectory += f"--- Reviewer Feedback ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self) -> str:
        """Get the most recent execution result"""
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return ""


class ReflectionAgent(Agent):
    """
    Reflection Agent - An agent capable of self-reflection and iterative refinement.

    This agent can:
    1. Execute the initial task
    2. Reflect on the result
    3. Refine based on reflection
    4. Iterate until satisfactory

    Particularly suited for code generation, document writing, analytical reports,
    and other tasks that benefit from iterative refinement.

    Supports multiple domain-specific prompt templates; users can customize or use built-in templates.
    """

    def __init__(
        self,
        name: str,
        llm: MiniAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_iterations: int = 3,
        custom_prompts: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the ReflectionAgent.

        Args:
            name: Agent name
            llm: LLM instance
            system_prompt: System prompt
            config: Configuration object
            max_iterations: Maximum number of iterations
            custom_prompts: Custom prompt templates {"initial": "", "reflect": "", "refine": ""}
        """
        super().__init__(name, llm, system_prompt, config)
        self.max_iterations = max_iterations
        self.memory = Memory()
        self.prompts = custom_prompts if custom_prompts else DEFAULT_PROMPTS

    def run(self, input_text: str, **kwargs) -> str:
        """
        Run the Reflection Agent.

        Args:
            input_text: Task description
            **kwargs: Additional parameters

        Returns:
            The final refined result
        """
        print(f"\n[Agent] {self.name} starting task: {input_text}")

        # Reset memory
        self.memory = Memory()

        # 1. Initial execution
        print("\n--- Initial Attempt ---")
        initial_prompt = self.prompts["initial"].format(task=input_text)
        initial_result = self._get_llm_response(initial_prompt, **kwargs)
        self.memory.add_record("execution", initial_result)

        # 2. Iteration loop: reflect and refine
        for i in range(self.max_iterations):
            print(f"\n--- Iteration {i+1}/{self.max_iterations} ---")

            # a. Reflect
            print("\n-> Reflecting...")
            last_result = self.memory.get_last_execution()
            reflect_prompt = self.prompts["reflect"].format(
                task=input_text, content=last_result
            )
            feedback = self._get_llm_response(reflect_prompt, **kwargs)
            self.memory.add_record("reflection", feedback)

            # b. Check if we should stop
            if "no improvement needed" in feedback.lower():
                print(
                    "\n[Agent] Reflection indicates no further improvement needed. Task complete."
                )
                break

            # c. Refine
            print("\n-> Refining...")
            refine_prompt = self.prompts["refine"].format(
                task=input_text, last_attempt=last_result, feedback=feedback
            )
            refined_result = self._get_llm_response(refine_prompt, **kwargs)
            self.memory.add_record("execution", refined_result)

        final_result = self.memory.get_last_execution()
        print(f"\n--- Task Complete ---\nFinal Result:\n{final_result}")

        # Save to history
        self.add_to_history(Message(content=input_text, role="user"))
        self.add_to_history(Message(content=final_result, role="assistant"))

        return final_result

    def _get_llm_response(self, prompt: str, **kwargs) -> str:
        """Call the LLM and get the complete response"""
        messages = [Message(content=prompt, role="user")]
        chunks = []
        for chunk in self.llm.stream(messages, **kwargs):
            chunks.append(chunk)
        response_text = "".join(chunks) if chunks else ""
        return response_text
