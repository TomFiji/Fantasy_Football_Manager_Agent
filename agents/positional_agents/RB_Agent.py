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

box_scores = league.box_scores(int(league.current_week)-3)
for matchup in box_scores:
    if matchup.home_team == my_team or matchup.away_team == my_team:
        my_lineup = matchup.home_lineup if matchup.home_team == my_team else matchup.away_lineup

my_rb_players = []
for player in my_team.roster:
    if (player.position == 'RB' and player.on_bye_week==False):
        my_rb_players.append(player)

def get_RB_aggregate_stats(player: str):
    p = league.player_info(name=player)
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
    
def get_RB_average_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    weeksPlayed = stats['breakdown'].get('210', 0)
    if (weeksPlayed == 0):
        return "No games played"
    else:
        return{
            "Season Average Rushing Attempts": stats['breakdown'].get('rushingAttempts',0)/weeksPlayed,
            "Season Average Rushing Yards Per Attempt": stats['breakdown'].get('rushingYardsPerAttempt',0),
            "Season Average Receptions": stats['breakdown'].get('receivingReceptions',0)/weeksPlayed,
            "Season Average Targets": stats['breakdown'].get('receivingTargets', 0)/weeksPlayed,
            "Season Average Rushing Yards": stats['breakdown'].get('rushingYards', 0),
            "Season Average Receiving Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0)/weeksPlayed,
            "Season Average Rushing Touchdowns": stats['breakdown'].get('rushingTouchdowns', 0)/weeksPlayed,
            "Season Average Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0)/weeksPlayed,
            "Season Average Fumbles": stats['breakdown'].get('fumbles', 0)/weeksPlayed,
            "Season Average First Downs": stats['breakdown'].get('213', 0)/weeksPlayed,
        }

def get_RB_week_stats(player: str, week: int):
    p = league.player_info(name=player)
    stats = p.stats.get(week, "Not available")
    return{
        f"Week {week} Rushing Attempts": stats['breakdown'].get('rushingAttempts',0),
        f"Week {week} Rushing Yards Per Attempt": stats['breakdown'].get('rushingYardsPerAttempt',0),
        f"Week {week} Receptions": stats['breakdown'].get('receivingReceptions',0),
        f"Week {week} Targets": stats['breakdown'].get('receivingTargets', 0),
        f"Week {week} Rushing Yards": stats['breakdown'].get('rushingYards', 0),
        f"Week {week} Receiving Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
        f"Week {week} Rushing Touchdowns": stats['breakdown'].get('rushingTouchdowns', 0),
        f"Week {week} Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
        f"Week {week} Fumbles": stats['breakdown'].get('fumbles', 0),
        f"Week {week} First Downs": stats['breakdown'].get('213', 0),
        f"Week {week} 100-199 Rushing Yard Game": stats['breakdown'].get('rushing100To199YardGame',0),
        f"Week {week} 200+ Rushing Yard Game": stats['breakdown'].get('rushing200PlusYardGame',0),
        f"Week {week} Touchdowns with 40-49 Yards Rushing": (stats['breakdown'].get('rushing40PlusYardTD',0)-stats['breakdown'].get('rushing50PlusYardTD', 0)),
        f"Week {week} Touchdowns with 50+ Yards Rushing": stats['breakdown'].get('rushing50PlusYardTD', 0),
        f"Week {week} Every 5 Receptions": stats['breakdown'].get('54',0),
        f"Week {week} Every 10 Receptions": stats['breakdown'].get('55',0),
    }        
       