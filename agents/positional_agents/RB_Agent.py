from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_weekly_stats, search_web, get_player_list_info, post_week_stats
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

rb_agent = LlmAgent(
    name="wr_agent",
    model=Gemini(model="gemini-2.5-pro", retry_options=retry_config),
    instruction=f"""You are the running back coordinator of my fantasy football team.
    
    Your job is to choose to pick the 2 best options from a list of running back I give you. For each player in {rb_list} you will:
    1. Call 'get_RB_aggregate_stats' using the value found in player_id as the parameter to access the data
    2. Call 'get_RB_average_stats' using the value found in player_id as the parameter to access the data
    2. Call 'get_player_weekly_stats' 4 times for each player's PREVIOUS 4 weeks to 'get_current_week'. DO NOT call get_current_week's stats, it will result in an error.
        a. For example, 'get_current_week' returns 11, pull up weeks 7-10
        b. If 'get_current_week' is less than 5, only pull up the weeks previous to that. DO NOT pass through 0 or any negative numbers through the function
        c. Do not analyze the week a player was on the bench or BYE
    3. Analyze each player's stats from the multiple dictionaries you just pulled and grade them on a scale of 0-100 based on the stats given to you of that player
    4. For each player, also take into consideration their injury status and use 'search_web' to do more analysis if injury status isn't 'ACTIVE' and change their grade accordingly
    5. For each player, also take into consideration their 'Opposing team' and 'Opposing team's defensive rank against WRs' from {rb_list} and change their grade accordingly
    6. For each player, use 'search_web' to look up the strength of their team's offensive line and put emphasis on this for their grade since a good offensive line is a must for a good running performance
    7. For each player, grab their 'Team' from {rb_list} and use 'search_web' to see if there are any other injured running backs on the team that are out or running backs coming back. Use this information to update that player's grade.
    
    **Output Format**
    - Rank players from 1 to however many running backs are on the roster and the grade you gave them
    - For top 2: "START" with reason
    - For others: "SIT" with brief explanation
    - Include key stats supporting each decision
    - Note any concerns (e.g. TD-dependent, low floor, running back room, o-line health, vegas odds, etc.)
    """,
    tools=[
        FunctionTool(get_current_week),
        FunctionTool(get_RB_aggregate_stats),
        FunctionTool(get_RB_average_stats),
        FunctionTool(get_player_weekly_stats),
        FunctionTool(search_web)
    ]
)

rb_runner = InMemoryRunner(agent=rb_agent)

async def test_agent():
    response = await rb_runner.run_debug("What running backs should I start this week?")

asyncio.run(test_agent())          