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

te_list = get_player_list_info('TE')


def get_TE_aggregate_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    return{
        "Season Total Receptions": stats['breakdown'].get('receivingReceptions',0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total Receiving Yards": math.ceil(stats['breakdown'].get('receivingYards', 0)*stats['breakdown'].get('210', 0)),
        "Season Total Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
        "Season Total Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
        "Season Total Targets": stats['breakdown'].get('receivingTargets', 0),
        "Season Total Receiving First Downs": stats['breakdown'].get('213', 0),
        "Season Total 100-199 Receiving Yard Games": stats['breakdown'].get('receiving100To199YardGame',0),
        "Season Total Touchdowns with 0-9 Yard Reception": stats['breakdown'].get('183',0),
        "Season Total Touchdowns with 10-19 Yard Reception": stats['breakdown'].get('184',0),
        "Season Total Touchdowns with 20-29 Yard Reception": stats['breakdown'].get('185',0),
        "Season Total Touchdowns with 30-39 Yard Reception": stats['breakdown'].get('186',0),
        "Season Total Touchdowns with 40-49 Yard Reception": (stats['breakdown'].get('receiving40PlusYardTD',0)-stats['breakdown'].get('receiving50PlusYardTD', 0)),
        "Season Total Touchdowns with 50+ Yard Reception": stats['breakdown'].get('receiving50PlusYardTD', 0),
        "Every 5 Receptions": stats['breakdown'].get('54',0),
        "Every 10 Receptions": stats['breakdown'].get('55',0),
        "Every 5 Receiving Yards": stats['breakdown'].get('47', 0),
        "Every 10 Receiving Yards": stats['breakdown'].get('48', 0),
        "Every 20 Receiving Yards": stats['breakdown'].get('49', 0),
        "Every 25 Receiving Yards": stats['breakdown'].get('50', 0),
        "Every 50 Receiving Yards": stats['breakdown'].get('51', 0),
        "Every 100 Receiving Yards": stats['breakdown'].get('52', 0),
        "Catch Rate Percentage": round((stats['breakdown'].get('receivingReceptions' ,0)/stats['breakdown'].get('receivingTargets' ,0) if stats['breakdown'].get('receivingTargets' ,0) != 0 else 0),2),
        "Fantasy Points Per Target": round((stats.get('points' ,0)/stats['breakdown'].get('receivingTargets' ,0) if stats['breakdown'].get('receivingTargets' ,0) != 0 else 0),2),
        "Season Total Receiving 2 Point Conversions": stats['breakdown']['receiving 2PtConversions'], 
        "Season Total Fumbles": stats['breakdown'].get('fumbles'),
        "Season Total Receiving Fumbles": stats['breakdown'].get('67', 0),
        "Season Total Receiving Fumbles Lost": stats['breakdown'].get('71', 0),
        "Season Total Rushing Attempts": stats['breakdown'].get('rushingAttempts', 0),
        "Season Total Rushing Yards": math.ceil(stats['breakdown'].get('rushingYards', 0)*stats['breakdown'].get('210', 0)),
        "Season Total Rushing Touchdowns": stats['breakdown'].get('rushingTouchdowns', 0),
        "Total Games Played": stats['breakdown'].get('210', 0)
    }
    
def get_TE_average_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    weeksPlayed = stats['breakdown']['210']
    if (weeksPlayed == 0):
        return "No games played"
    else:
        return{
            "Season Average Receptions": round(stats['breakdown'].get('receivingReceptions',0)/weeksPlayed, 2),
            "Season Average Targets": round(stats['breakdown'].get('receivingTargets', 0)/weeksPlayed, 2),
            "Season Average Receiving Yards": round(stats['breakdown'].get('receivingYards', 0), 2),
            "Season Average Touchdowns": round(stats['breakdown'].get('receivingTouchdowns', 0)/weeksPlayed, 2),
            "Season Average Yards After Catch": round(stats['breakdown'].get('receivingYardsAfterCatch', 0)/weeksPlayed, 2),
            "Season Average Targets": round(stats['breakdown'].get('receivingTargets', 0)/weeksPlayed, 2),
            "Receiving Yards Per Reception": round(stats['breakdown'].get('receivingYardsPerReception', 0), 2),
            "Season Average Receiving First Downs": round(stats['breakdown'].get('213', 0)/weeksPlayed, 2),
            "Season Average 100-199 Receiving Yard Games": round(stats['breakdown'].get('receiving100To199YardGame',0)/weeksPlayed, 2),
            "Season Average Receiving 2 Point Conversions": round(stats['breakdown'].get('receiving 2PtConversions', 0)/weeksPlayed, 2),
            "Season Average Fumbles": round(stats['breakdown'].get('fumbles')/weeksPlayed, 2),
            "Season Average Receiving Fumbles": round(stats['breakdown'].get('67', 0), 2),
            "Season Average Receiving Fumbles Lost": round(stats['breakdown'].get('71', 0), 2),
            "Season Average Rushing Attempts": round(stats['breakdown'].get('rushingAttempts', 0), 2),
            "Season Average Rushing Yards": round(math.ceil(stats['breakdown'].get('rushingYards', 0)*stats['breakdown'].get('210', 0)), 2),
            "Season Average Rushing Touchdowns": round(stats['breakdown'].get('rushingTouchdowns', 0), 2),
        }
    
for player in wr_list:
    post_week_stats(player, 'WR')


wr_agent = LlmAgent(
    name="wr_agent",
    model=Gemini(model="gemini-2.5-pro", retry_options=retry_config),
    instruction=f"""You are the wide receiver coordinator of my fantasy football team.
    
    Your job is to choose to pick the 2 best options from a list of wide receivers I give you. For each player in {wr_list} you will:
    1. Call 'get_WR_aggregate_stats' using the value found in player_id as the parameter to access the data
    2. Call 'get_WR_average_stats' using the value found in player_id as the parameter to access the data
    2. Call 'get_player_weekly_stats' 4 times for each player's PREVIOUS 4 weeks to 'get_current_week'. DO NOT call get_current_week's stats, it will result in an error.
        a. For example, 'get_current_week' returns 11, pull up weeks 7-10
        b. If 'get_current_week' is less than 5, only pull up the weeks previous to that. DO NOT pass through 0 or any negative numbers through the function
        a. Do not analyze the week a player was on the bench or BYE
    3. Analyze each player's stats from the multiple dictionaries you just pulled and grade them on a scale of 0-100 based on the stats given to you of that player
    4. For each player, also take into consideration their injury status and use 'search_web' to do more analysis if injury status isn't 'ACTIVE' and change their grade accordingly
    5. For each player, also take into consideration their 'Opposing team' and 'Opposing team's defensive rank against WRs' from {wr_list} and change their grade accordingly
    6. For each player, use 'search_web' to look up the strength of their team's offensive line
    7. For each player, grab their 'Team' from {wr_list} and use 'search_web' to see if there are any other injured wide receivers on the team that are out or wide receivers coming back. Use this information to update that player's grade.
    
    **Output Format**
    - Rank players from 1 to however many wide receivers are on the roster and the grade you gave them
    - For top 2: "START" with reason
    - For others: "SIT" with brief explanation
    - Include key stats supporting each decision
    - Note any concerns (e.g. TD-dependent, low floor, wide receiver room, o-line health, vegas odds, etc.)
    """,
    tools=[
        FunctionTool(get_current_week),
        FunctionTool(get_WR_aggregate_stats),
        FunctionTool(get_WR_average_stats),
        FunctionTool(get_player_weekly_stats),
        FunctionTool(search_web)
    ]
)

wr_runner = InMemoryRunner(agent=wr_agent)

async def test_agent():
    response = await wr_runner.run_debug("What wide receivers should I start this week?")

asyncio.run(test_agent())         