from dotenv import load_dotenv
from mini_agents import PlanAndSolveAgent, MiniAgentsLLM

load_dotenv()

def main():
    llm_client = MiniAgentsLLM()
    plan_solve_agent = PlanAndSolveAgent(name="plan_solve_agent", llm_client=llm_client)
    question = "How to transition from being a frontend developer to full-stack developer?Keep your response brief and to the point."
    plan_solve_agent.run(question)

if __name__ == "__main__":    
    main()
