from dotenv import load_dotenv
import os
import sys
import logging
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
from google.adk.runners import InMemoryRunner

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from google.adk.apps.app import App, ResumabilityConfig
from google.adk.tools.function_tool import FunctionTool
from googlesearch import search

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
#                     format='%(levelname)s: %(message)s')


wr_list = get_player_list_info('WR')
current_week = get_current_week()

        
# for player in wr_list:
#     post_week_stats(player, "WR")
#     print(f"Name: {player['player_name']}, Stats: {get_aggregate_stats(player, 'WR')}")




wr_agent = LlmAgent(
    name="wr_agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config, temperature=0.0),
    instruction=f"""You are the wide receiver coordinator of my fantasy football team. Your goal is to choose the 2 best options.
    
    For **EACH** player in the {wr_list}:
    1. Retrieve the player's core season metrics: Call 'get_aggregate_stats' and 'get_average_stats' using the value found in player_id and position='WR' as the parameters to access the data
    2. Retrieve the player's recent performance: Call 'get_player_recent_performance' using their player_id.
        a. Do not analyze the week a player was on the bench or BYE
    3. Retrieve External Context: Call 'search_tool' to research the player's injury status, team offensive line strength, and critical teammate's health. This information has to be relevant to week {current_week} of the current 2025/2026 season, ignore all information from other seasons as the rosters have changed. Use this information to determine if the player's usage will increase or decrease this week.
    4. The opponent's defensive rank and the player's injury status (from the input list) are critical factors.
    5. Analyze ALL retrieved data (stats, opponents' rank, and web search results) and assign a grade from 0-100.

    
    **Output Format**
    **MUST BE IN VALID JSON ARRAY FORMAT WITH NO MARKDOWN FORMATTING OR CODE BLOCKS**      
    Return a JSON array containing ALL players:
    [
        {{

            "rank": 'rank out of all the players',
            "player_name": 'player name',
            "player_id": 'player id',
            "player_grade": 'player grade',
            "recommendation": 'START or SIT',
            "opponent": 'opponent team name',
            "opponent_ranking_against_WR": 'opponent ranking'
            "reasoning": 'reasoning'

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

wr_runner = InMemoryRunner(agent=wr_agent, app_name='agents')

if __name__ == "__main__":
    async def test_agent():
        response = await wr_runner.run_debug("What wide receivers should I start this week?")

    asyncio.run(test_agent())    