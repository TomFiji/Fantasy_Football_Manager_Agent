from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league

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



retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# box_scores = league.box_scores(int(league.current_week)-3)
# for matchup in box_scores:
#     if matchup.home_team == my_team or matchup.away_team == my_team:
#         my_lineup = matchup.home_lineup if matchup.home_team == my_team else matchup.away_lineup



# my_wr_players = []
# for player in my_team.roster:
#     if (player.position == 'WR'):
#         my_wr_players.append(player)

# print(my_wr_players)
# def get_wr_stats() -> dict:
    
player = league.player_info(name="Nico Collins")
print("\Aggregate Stats: ", player.stats.get(0, "Not available")) 
print("\nWeek 3 Stats: ", player.stats.get(3, "Not available"))    