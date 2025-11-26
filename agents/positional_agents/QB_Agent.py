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

qb_list = get_player_list_info('QB')

def get_QB_aggregate_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    return{
        "Season Total Passing Attempts": stats['breakdown'].get('passingAttempts',0),
        "Season Total Passing Completions": stats['breakdown'].get('passingCompletions',0),
        "Season Total Passing Completion Percentage": stats['breakdown'].get('passingCompletionPercentage',0),
        "Every 5 Pass Completions": stats['breakdown'].get('11', 0),
        "Every 10 Pass Completions": stats['breakdown'].get('12', 0),
        "Season Total Passing Yards": round((stats['breakdown'].get('passingYards', 0)*stats['breakdown'].get('210', 0)), 2),
        "Every 5 Passing Yards": stats['breakdown'].get('5', 0),
        "Every 10 Passing Yards": stats['breakdown'].get('6', 0),
        "Every 20 Passing Yards": stats['breakdown'].get('7', 0),
        "Every 25 Passing Yards": stats['breakdown'].get('8', 0),
        "Every 50 Passing Yards": stats['breakdown'].get('9', 0),
        "Every 100 Passing Yards": stats['breakdown'].get('10', 0),
        "Season Total Games with 300-399 Passing Yards": stats['breakdown'].get('passing300To399YardGame', 0),
        "Season Total Games with 400+ Passing Yards": stats['breakdown'].get('passing400PlusYardGame', 0),
        "Season Total Passing Touchdowns": stats['breakdown'].get('passingTouchdowns',0),
        "Season Total Passing 2 Point Conversions": stats['breakdown'].get('passing2PtConversions' ,0),
        "Season Total Rushing 2 Point Conversions": stats['breakdown'].get('rushing2PtConversions' ,0),
        "Season Total Passing Interceptions": stats['breakdown'].get('passingInterceptions' ,0),
        "Season Total Times Sacked Passing": stats['breakdown'].get('passingTimesSacked' ,0),
        "Season Total Passing Fumbles": stats['breakdown'].get('65' ,0),
        "Season Total Turnovers": stats['breakdown'].get('turnovers' ,0),
        "Season Total Games Played": stats['breakdown'].get('210' ,0),
        "Season Total Passing First Downs": stats['breakdown'].get('211' ,0),
        "Season Total Rush Attempts": stats['breakdown'].get('rushingAttempts' ,0),
        "Season Total Rushing Yards": math.ceil(stats['breakdown'].get('rushingYards', 0)*stats['breakdown'].get('210', 0)),
        "Season Total Rushing Touchdowns": stats['breakdown'].get('rushingTouchdowns' ,0),
        "Every 5 Rushing Yards": stats['breakdown'].get('27' ,0),
        "Every 10 Rushing Yards": stats['breakdown'].get('28' ,0),
        "Every 20 Rushing Yards": stats['breakdown'].get('29' ,0),
        "Every 25 Rushing Yards": stats['breakdown'].get('30' ,0),
        "Every 50 Rushing Yards": stats['breakdown'].get('31' ,0),
        "Every 100 Rushing Yards": stats['breakdown'].get('32' ,0),
        "Rushing Yards Per Attempt": stats['breakdown'].get('rushingYardsPerAttempt' ,0),
    }
    
def get_QB_average_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    weeksPlayed = stats['breakdown']['210']
    if (weeksPlayed == 0):
        return "No games played"
    else:
        return{
            "Season Average Passing Attempts": round(stats['breakdown'].get('passingAttempts',0)/weeksPlayed, 2),
            "Season Average Passing Completions": round(stats['breakdown'].get('passingCompletions',0)/weeksPlayed, 2),
            "Season Average Passing Completion Percentage": round(stats['breakdown'].get('passingCompletionPercentage',0)/weeksPlayed, 2),
            "Season Average Every 5 Pass Completions": round(stats['breakdown'].get('11', 0)/weeksPlayed, 2),
            "Season Average Every 10 Pass Completions": round(stats['breakdown'].get('12', 0)/weeksPlayed, 2),
            "Season Average Passing Yards": round(stats['breakdown'].get('passingYards', 0), 2),
            "Season Average Games with 300-399 Passing Yards": round(stats['breakdown'].get('passing300To399YardGame', 0)/weeksPlayed, 2),
            "Season Average Games with 400+ Passing Yards": round(stats['breakdown'].get('passing400PlusYardGame', 0)/weeksPlayed, 2),
            "Season Average Passing Touchdowns": round(stats['breakdown'].get('passingTouchdowns',0)/weeksPlayed, 2),
            "Season Average Passing 2 Point Conversions": round(stats['breakdown'].get('passing2PtConversions' ,0)/weeksPlayed, 2),
            "Season Average Rushing 2 Point Conversions": round(stats['breakdown'].get('rushing2PtConversions' ,0)/weeksPlayed, 2),
            "Season Average Passing Interceptions": round(stats['breakdown'].get('passingInterceptions' ,0)/weeksPlayed, 2),
            "Season Average Times Sacked Passing": round(stats['breakdown'].get('passingTimesSacked' ,0)/weeksPlayed, 2),
            "Season Average Passing Fumbles": round(stats['breakdown'].get('65' ,0)/weeksPlayed, 2),
            "Season Average Turnovers": round(stats['breakdown'].get('turnovers' ,0)/weeksPlayed, 2),
            "Season Average Passing First Downs": round(stats['breakdown'].get('211' ,0)/weeksPlayed, 2),
            "Season Average Rush Attempts": round(stats['breakdown'].get('rushingAttempts' ,0)/weeksPlayed, 2),
            "Season Average Rushing Yards": round(stats['breakdown'].get('rushingYards', 0), 2),
            "Season Average Rushing Touchdowns": round(stats['breakdown'].get('rushingTouchdowns' ,0)/weeksPlayed, 2),
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