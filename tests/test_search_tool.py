from dotenv import load_dotenv
from mini_agents.tools.builtin.search_tool import (
    SearchTool,
    search_tavily,
    search_serpapi,
)

load_dotenv()

search_tool = SearchTool()
question = "When is The White Lotus Season 4 released?"

# Test hybrid mode
hybrid_mode_result = search_tool.run(
    {"input": question, "backend": "hybrid", "mode": "structured"}
)
print(hybrid_mode_result)

# Test Tavily mode
tavilty_mode_result = search_tavily(question)
print(tavilty_mode_result)

# Test SerpApi mode
serppapi_mode_result = search_serpapi(question)
print(serppapi_mode_result)
