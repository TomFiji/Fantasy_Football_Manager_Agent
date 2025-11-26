from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_weekly_stats, search_web, get_player_list_info
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
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
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


wr_list = get_player_list_info('WR')

def get_WR_aggregate_stats(player_id: int) -> dict:
    p = league.player_info(playerId=player_id)
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
        "Catch Rate Percentage": round((stats['breakdown'].get('receivingReceptions' ,0)/stats['breakdown'].get('receivingTargets' ,0) if stats['breakdown'].get('receivingTargets' ,0) != 0 else 0),2),
        "Fantasy Points Per Target": round((stats.get('points' ,0)/stats['breakdown'].get('receivingTargets', 0) if stats['breakdown'].get('receivingTargets' ,0) != 0 else 0),2)   
    }

def get_WR_average_stats(player_id: int) -> dict:
    p = league.player_info(playerId=player_id)
    stats = p.stats.get(0, "Not available")
    weeksPlayed = stats['breakdown'].get('210', 0)
    if (weeksPlayed == 0):
        return "No games played"
    else:
        return{
        "Season Average Receptions": round(stats['breakdown'].get('receivingReceptions',0)/weeksPlayed, 2),
        "Season Average Targets": round(stats['breakdown'].get('receivingTargets', 0)/weeksPlayed, 2),
        "Season Average Receiving Yards": round(stats['breakdown'].get('receivingYards', 0), 2),
        "Season Average Receiving Yards Per Reception": round(stats['breakdown'].get('receivingYardsPerReception', 0), 2),
        "Season Average Touchdowns": round(stats['breakdown'].get('receivingTouchdowns', 0)/weeksPlayed, 2),
        "Season Average Yards After Catch": round(stats['breakdown'].get('receivingYardsAfterCatch', 0)/weeksPlayed, 2),
        "Season Average Targets": round(stats['breakdown'].get('receivingTargets', 0)/weeksPlayed, 2),
        "Season Average Receiving First Downs": round(stats['breakdown'].get('213', 0)/weeksPlayed, 2),
        "Season Average 100-199 Receiving Yard Games": round(stats['breakdown'].get('receiving100To199YardGame',0)/weeksPlayed, 2),
    }

def post_WR_week_stats(player):
    p = league.player_info(playerId=player["player_id"])
    if league.current_week<5:
        week_range = range(1, league.current_week)
    else:
        week_range = range(league.current_week-4, league.current_week)
    for week in week_range:
        response = (
            supabase.table("player_weekly_stats")
            .select("*")  # Just select one column (faster)
            .eq("player_id", player["player_id"])
            .eq("week", week)
            .execute()
        )
        if response.data:
            pass
        else:
            stats = p.stats.get(week, "Not available")
            if (stats == "Not available"): 
                data = {f"Week {week} Stats": "Didn't play because they were benched or on BYE week."}
            else:
                data = {
                    f"Week {week} Receptions": stats['breakdown'].get('receivingReceptions',0),
                    f"Week {week} Targets": stats['breakdown'].get('receivingTargets', 0),
                    f"Week {week} Receiving Yards": stats['breakdown'].get('receivingYards', 0),
                    f"Week {week} Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
                    f"Week {week} Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
                    f"Week {week} First Downs": stats['breakdown'].get('213', 0),
                    f"Week {week} Touchdowns with 0-9 Yard Reception": stats['breakdown'].get('183',0),
                    f"Week {week} Touchdowns with 10-19 Yard Reception": stats['breakdown'].get('184',0),
                    f"Week {week} Touchdowns with 20-29 Yard Reception": stats['breakdown'].get('185',0),
                    f"Week {week} Touchdowns with 30-39 Yard Reception": stats['breakdown'].get('186',0),
                    f"Week {week} Touchdowns with 40-49 Yard Reception": (stats['breakdown'].get('receiving40PlusYardTD',0)-stats['breakdown'].get('receiving50PlusYardTD', 0)),
                    f"Week {week} Touchdowns with 50+ Yard Reception": stats['breakdown'].get('receiving50PlusYardTD', 0),
                    f"Week {week} Every 5 Receptions": stats['breakdown'].get('54',0),
                    f"Week {week} Every 10 Receptions": stats['breakdown'].get('55',0),
                    f"Week {week} Catch Rate Percentage": round((stats['breakdown'].get('receivingReceptions' ,0)/stats['breakdown'].get('receivingTargets' ,0) if stats['breakdown'].get('receivingTargets' ,0) != 0 else 0),2),
                    f"Week {week} Fantasy Points Per Target": round((stats.get('points' ,0)/stats['breakdown'].get('receivingTargets' ,0) if stats['breakdown'].get('receivingTargets' ,0) != 0 else 0),2)   
                }
            response = (
                supabase.table("player_weekly_stats")
                .insert({"player_id": player["player_id"], "week": week, "player_name": player["player_name"], "stats_breakdown": data, "points": stats.get('points', 0) if stats != 'Not available' else 0})
                .execute()
            )
            print(f"{player['player_name']} for week {week} added")
        
for player in wr_list:
    post_WR_week_stats(player)


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
    tools=[get_player_list_info, get_current_week, get_WR_aggregate_stats, get_WR_average_stats, get_player_weekly_stats, search_web]
)

# wr_runner = InMemoryRunner(agent=wr_agent)

# async def test_agent():
#     response = await wr_runner.run_debug("What wide receivers should I start this week?")

# asyncio.run(test_agent())    