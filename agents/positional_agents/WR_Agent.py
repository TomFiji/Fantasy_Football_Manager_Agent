from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
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
#     if (player.position == 'WR' AND MAKE SURE PLAYER IS NOT ON BYE):
#         my_wr_players.append(player)

# print(my_wr_players)
# def get_wr_stats() -> dict:
def get_WR_aggregate_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    return{
        "Season Total Receptions": stats['breakdown'].get('receivingReceptions',0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total Receiving Yards": math.ceil(stats['breakdown'].get('receivingYards', 0)*stats['breakdown'].get('210', 0)),
        "Season Total Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
        "Season Total Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
        "Receiving Yards Per Reception": stats['breakdown'].get('receivingYardsPerReception', 0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total First Downs": stats['breakdown'].get('213', 0),
        "Season Total 100-199 Receiving Yard Games": stats['breakdown'].get('receiving100To199YardGame',0),
        "Season Total Touchdowns with 0-9 Yard Reception": stats['breakdown'].get('183',0),
        "Season Total Touchdowns with 10-19 Yard Reception": stats['breakdown'].get('184',0),
        "Season Total Touchdowns with 20-29 Yard Reception": stats['breakdown'].get('185',0),
        "Season Total Touchdowns with 30-39 Yard Reception": stats['breakdown'].get('186',0),
        "Season Total Touchdowns with 40-49 Yard Reception": (stats['breakdown'].get('receiving40PlusYardTD',0)-stats['breakdown'].get('receiving50PlusYardTD', 0)),
        "Season Total Touchdowns with 50+ Yard Reception": stats['breakdown'].get('receiving50PlusYardTD', 0),
        "Every 5 Receptions": stats['breakdown'].get('54',0),
        "Every 10 Receptions": stats['breakdown'].get('55',0),
        "Catch Rate Percentage": round((stats['breakdown']['receivingReceptions']/stats['breakdown']['receivingTargets'] if stats['breakdown']['receivingTargets'] != 0 else 0),2),
        "Fantasy Points Per Target": round((stats['points']/stats['breakdown']['receivingTargets'] if stats['breakdown']['receivingTargets'] != 0 else 0),2)   
    }

def get_average_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    return{
        "Season Total Receptions": stats['breakdown'].get('receivingReceptions',0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total Receiving Yards": math.ceil(stats['breakdown'].get('receivingYards', 0)*stats['breakdown'].get('210', 0)),
        "Season Total Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
        "Season Total Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total First Downs": stats['breakdown'].get('213', 0),
        "Season Total 100-199 Receiving Yard Games": stats['breakdown'].get('receiving100To199YardGame',0),
        "Season Total Touchdowns with 0-9 Yard Reception": stats['breakdown'].get('183',0),
        "Season Total Touchdowns with 10-19 Yard Reception": stats['breakdown'].get('184',0),
        "Season Total Touchdowns with 20-29 Yard Reception": stats['breakdown'].get('185',0),
        "Season Total Touchdowns with 30-39 Yard Reception": stats['breakdown'].get('186',0),
        "Season Total Touchdowns with 40-49 Yard Reception": (stats['breakdown'].get('receiving40PlusYardTD',0)-stats['breakdown'].get('receiving50PlusYardTD', 0)),
        "Season Total Touchdowns with 50+ Yard Reception": stats['breakdown'].get('receiving50PlusYardTD', 0),
        "Every 5 Receptions": stats['breakdown'].get('54',0),
        "Every 10 Receptions": stats['breakdown'].get('55',0),
        "Catch Rate Percentage": round((stats['breakdown']['receivingReceptions']/stats['breakdown']['receivingTargets'] if stats['breakdown']['receivingTargets'] != 0 else 0),2),
        "Fantasy Points Per Target": round((stats['points']/stats['breakdown']['receivingTargets'] if stats['breakdown']['receivingTargets'] != 0 else 0),2)   
    }
    
def get_weekly_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    return{
        "Season Total Receptions": stats['breakdown'].get('receivingReceptions',0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total Receiving Yards": math.ceil(stats['breakdown'].get('receivingYards', 0)*stats['breakdown'].get('210', 0)),
        "Season Total Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
        "Season Total Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total First Downs": stats['breakdown'].get('213', 0),
        "Season Total 100-199 Receiving Yard Games": stats['breakdown'].get('receiving100To199YardGame',0),
        "Season Total Touchdowns with 0-9 Yard Reception": stats['breakdown'].get('183',0),
        "Season Total Touchdowns with 10-19 Yard Reception": stats['breakdown'].get('184',0),
        "Season Total Touchdowns with 20-29 Yard Reception": stats['breakdown'].get('185',0),
        "Season Total Touchdowns with 30-39 Yard Reception": stats['breakdown'].get('186',0),
        "Season Total Touchdowns with 40-49 Yard Reception": (stats['breakdown'].get('receiving40PlusYardTD',0)-stats['breakdown'].get('receiving50PlusYardTD', 0)),
        "Season Total Touchdowns with 50+ Yard Reception": stats['breakdown'].get('receiving50PlusYardTD', 0),
        "Every 5 Receptions": stats['breakdown'].get('54',0),
        "Every 10 Receptions": stats['breakdown'].get('55',0),
        "Catch Rate Percentage": round((stats['breakdown']['receivingReceptions']/stats['breakdown']['receivingTargets'] if stats['breakdown']['receivingTargets'] != 0 else 0),2),
        "Fantasy Points Per Target": round((stats['points']/stats['breakdown']['receivingTargets'] if stats['breakdown']['receivingTargets'] != 0 else 0),2)   
    }        

p = league.player_info(name="Mark Andrews")
stats = p.stats.get(0, "Not available")
week6stats = p.stats.get(10, "Not available")
print(stats)
#print(week6stats)