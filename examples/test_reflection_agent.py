from dotenv import load_dotenv
from mini_agents import ReflectionAgent, MiniAgentsLLM

load_dotenv()


def main():
    llm_client = MiniAgentsLLM()
    reflection_agent = ReflectionAgent(name="reflection_agent", llm=llm_client)
    question = "What is the correct point of contact for soccer shooting?"
    reflection_agent.run(question)

if __name__ == "__main__":
    main()
