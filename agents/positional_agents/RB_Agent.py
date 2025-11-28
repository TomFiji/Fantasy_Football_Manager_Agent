from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_recent_performance, get_player_list_info, post_week_stats, get_external_analysis, search_agent
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

def get_RB_aggregate_stats(player_id: int) -> dict:
    p = league.player_info(playerId=player_id)
    stats = p.stats.get(0, "Not available")
    return{
        "Season Total Rushing Attempts": stats['breakdown'].get('rushingAttempts',0),
        "Season Total Receptions": stats['breakdown'].get('receivingReceptions',0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total Rushing Yards": math.ceil(stats['breakdown'].get('rushingYards', 0)*stats['breakdown'].get('210', 0)),
        "Season Total Receiving Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
        "Season Total Rushing Touchdowns": stats['breakdown'].get('rushingTouchdowns', 0),
        "Season Total Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
        "Season Total Fumbles": stats['breakdown'].get('fumbles', 0),
        "Season Total First Downs": stats['breakdown'].get('213', 0),
        "Season Total 100-199 Rushing Yard Games": stats['breakdown'].get('rushing100To199YardGame',0),
        "Season Total 200+ Rushing Yard Games": stats['breakdown'].get('rushing200PlusYardGame',0),
        "Season Total Touchdowns with 40-49 Yards Rushing": (stats['breakdown'].get('rushing40PlusYardTD',0)-stats['breakdown'].get('rushing50PlusYardTD', 0)),
        "Season Total Touchdowns with 50+ Yards Rushing": stats['breakdown'].get('rushing50PlusYardTD', 0),
        "Season Total Touchdowns with 40-49 Yard Reception": (stats['breakdown'].get('receiving40PlusYardTD',0)-stats['breakdown'].get('receiving50PlusYardTD', 0)),
        "Season Total Touchdowns with 50+ Yard Reception": stats['breakdown'].get('receiving50PlusYardTD', 0),
        "Every 5 Receptions": stats['breakdown'].get('54',0),
        "Every 10 Receptions": stats['breakdown'].get('55',0),
    }
    
def get_RB_average_stats(player_id: int) -> dict:
    p = league.player_info(playerId=player_id)
    stats = p.stats.get(0, "Not available")
    weeksPlayed = stats['breakdown'].get('210', 0)
    if (weeksPlayed == 0):
        return "No games played"
    else:
        return{
            "Season Average Rushing Attempts": round(stats['breakdown'].get('rushingAttempts',0)/weeksPlayed, 2),
            "Season Average Rushing Yards Per Attempt": round(stats['breakdown'].get('rushingYardsPerAttempt',0), 2),
            "Season Average Receptions": round(stats['breakdown'].get('receivingReceptions',0)/weeksPlayed, 2),
            "Season Average Targets": round(stats['breakdown'].get('receivingTargets', 0)/weeksPlayed, 2),
            "Season Average Rushing Yards": round(stats['breakdown'].get('rushingYards', 0), 2),
            "Season Average Receiving Touchdowns": round(stats['breakdown'].get('receivingTouchdowns', 0)/weeksPlayed, 2),
            "Season Average Rushing Touchdowns": round(stats['breakdown'].get('rushingTouchdowns', 0)/weeksPlayed, 2),
            "Season Average Yards After Catch": round(stats['breakdown'].get('receivingYardsAfterCatch', 0)/weeksPlayed, 2),
            "Season Average Fumbles": round(stats['breakdown'].get('fumbles', 0)/weeksPlayed, 2),
            "Season Average First Downs": round(stats['breakdown'].get('213', 0)/weeksPlayed, 2),
        }

for player in rb_list:
    post_week_stats(player, 'RB')      

search_tool = AgentTool(agent=search_agent)

rb_agent = LlmAgent(
    name="rb_agent",
    model=Gemini(model="gemini-2.5-pro", retry_options=retry_config),
    instruction=f"""You are the running coordinator of my fantasy football team. Your goal is to choose the 2 best options.
    
    For **EACH** player in the {rb_list}:
    1. Retrieve the player's core season metrics: Call 'get_RB_aggregate_stats' and 'get_RB_average_stats' using the value found in player_id as the parameter to access the data
    2. Retrieve the player's recent performance: Call 'get_player_recent_performance' using their player_id.
        a. Do not analyze the week a player was on the bench or BYE
    3. Retrieve External Context: Call 'search_tool' to research the player's injury status, team offensive line strength, and critical teammate's health. This information has to be relevant the current week of the current 2025/2026 season, ignore all information from other seasons as the rosters have changed. Use this information to determine if the player's usage will increase or decrease this week.
    4. The opponent's defensive rank and the player's injury status (from the input list) are critical factors.
    5. Analyze ALL retrieved data (stats, opponents' rank, and web search results) and assign a grade from 0-100.

    
    **Output Format**
    - Rank players 1 to N, including the final 0-100 grade.
    - For top 2: "START" with the detailed reason, citing external factors and key stats.
    - For others: "SIT" with a brief explanation.
    - Note any specific concerns (e.g., o-line health, running back room, TD-dependency).
    """,
    tools=[
        FunctionTool(get_current_week),
        FunctionTool(get_RB_aggregate_stats),
        FunctionTool(get_RB_average_stats),
        FunctionTool(get_player_recent_performance),
        search_tool
    ]
)

rb_runner = InMemoryRunner(agent=rb_agent)

async def test_agent():
    response = await rb_runner.run_debug("What running backs should I start this week?")

asyncio.run(test_agent())