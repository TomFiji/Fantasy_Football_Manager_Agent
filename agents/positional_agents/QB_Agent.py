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
from google.adk.tools.agent_tool import AgentTool

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

def get_QB_aggregate_stats(player_id: int) -> dict:
    p = league.player_info(playerId=player_id)
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
    
def get_QB_average_stats(player_id: int) -> dict:
    p = league.player_info(playerId=player_id)
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

for player in qb_list:
    post_week_stats(player, 'QB')


search_tool = AgentTool(agent=search_agent)


qb_agent = LlmAgent(
    name="qb_agent",
    model=Gemini(model="gemini-2.5-pro", retry_options=retry_config),
    instruction=f"""You are the quarterback coordinator of my fantasy football team. Your goal is to choose the best option.
    
    For **EACH** player in {qb_list}:
    1. Retrieve the player's core season metrics: Call 'get_QB_aggregate_stats' and 'get_QB_average_stats' using the value found in player_id as the parameter to access the data
    2. Retrieve the player's recent performance: Call 'get_player_recent_performance' using their player_id.
        a. Do not analyze the week a player was on the bench or BYE
    3. Retrieve External Context: Call 'search_tool' to research the player's injury status, team offensive line strength, and critical teammate's health. This information has to be relevant the current week of the current 2025/2026 season, ignore all information from other seasons as the rosters have changed.
    4. The opponent's defensive rank and the player's injury status (from the input list) are critical factors.
    5. Analyze ALL retrieved data (stats, opponents' rank, and web search results) and assign a grade from 0-100.

    
   **Output Format**
    **MUST BE IN VALID JSON FORMAT**
    {{
        'rankings':[
            {{
                'rank': 'rank out of all the players',
                'player_name': 'player name',
                'player_id': 'player id',
                'player_grade': 'player grade',
                'recommendation': 'START or SIT',
                'opponent': 'opponent team name',
                'opponent ranking against QB': 'opponent ranking'
                'reasoning': 'reasoning'
            }}
        ]
    }}
    """,
    tools=[
        FunctionTool(get_current_week),
        FunctionTool(get_QB_aggregate_stats),
        FunctionTool(get_QB_average_stats),
        FunctionTool(get_player_recent_performance),
        search_tool
    ]
)

qb_runner = InMemoryRunner(agent=qb_agent)

async def test_agent():
    response = await qb_runner.run_debug("What quarterbacks should I start this week?")

asyncio.run(test_agent())     