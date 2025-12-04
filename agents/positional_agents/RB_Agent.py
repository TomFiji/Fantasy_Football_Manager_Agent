from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_recent_performance, get_player_list_info, post_week_stats, get_aggregate_stats, get_average_stats, search_tool
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from supabase_client import supabase


load_dotenv()

api_key = os.environ['GOOGLE_API_KEY']


import uuid
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from google.adk.apps.app import App, ResumabilityConfig
from google.adk.tools.function_tool import FunctionTool
from google.adk.runners import InMemoryRunner
from google.adk.tools.agent_tool import AgentTool



retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

rb_list = get_player_list_info('RB')
current_week = get_current_week()


rb_agent = LlmAgent(
    name="rb_agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config, temperature=0.0),
    instruction=f"""You are the running coordinator of my fantasy football team.

    Analyze ALL players in the roster and rank them. Mark the top 2 players as 'START' and the rest as 'SIT'.

    For **EACH** player in the {rb_list}:
    1. Retrieve the player's core season metrics: Call 'get_aggregate_stats' and 'get_average_stats' using the value found in player_id and position='RB' as the parameters to access the data
    2. Retrieve the player's recent performance: Call 'get_player_recent_performance' using their player_id.
        a. Do not analyze the week a player was on the bench or BYE
    3. Retrieve External Context: Call 'search_tool' to research the player's injury status, team offensive line strength, and critical teammate's health. This information has to be relevant to week {current_week} of the current 2025/2026 season, ignore all information from other seasons as the rosters have changed. Use this information to determine if the player's usage will increase or decrease this week.
    4. The opponent's defensive rank and the player's injury status (from the input list) are critical factors.
    5. Analyze ALL retrieved data (stats, opponents' rank, and web search results) and assign a grade from 0-100.

    
    **Output Format**
    **CRITICAL: Return ONLY a single JSON array - do NOT repeat or duplicate the array**
    **MUST BE IN VALID JSON ARRAY FORMAT WITH NO MARKDOWN, NO CODE BLOCKS, NO ADDITIONAL TEXT**

    Return ONE JSON array containing ALL players ONCE:
    [
        {{
            "rank": 1,
            "player_name": "player name",
            "player_id": "player id",
            "player_grade": 85,
            "recommendation": "START",
            "opponent": "opponent team name",
            "opponent_ranking_against_RB": 15,
            "reasoning": "detailed reasoning"
        }},
        {{
            "rank": 2,
            "player_name": "player name",
            "player_id": "player id",
            "player_grade": 75,
            "recommendation": "SIT",
            "opponent": "opponent team name",
            "opponent_ranking_against_RB": 10,
            "reasoning": "detailed reasoning"
        }}
    ]

    DO NOT output this array more than once. Return ONLY the JSON array with no additional text before or after.
    """,
    tools=[
        FunctionTool(get_current_week),
        FunctionTool(get_aggregate_stats),
        FunctionTool(get_average_stats),
        FunctionTool(get_player_recent_performance),
        search_tool
    ]
)

rb_runner = InMemoryRunner(agent=rb_agent, app_name='agents')

if __name__ == "__main__":
    async def test_agent():
        await rb_runner.run_debug("What running backs should I start this week?")

    asyncio.run(test_agent())