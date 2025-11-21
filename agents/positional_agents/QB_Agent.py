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

box_scores = league.box_scores(int(league.current_week))
for matchup in box_scores:
    if matchup.home_team == my_team or matchup.away_team == my_team:
        my_lineup = matchup.home_lineup if matchup.home_team == my_team else matchup.away_lineup

my_qb_players = []
for player in my_team.roster:
    if (player.position == 'QB' and player.on_bye_week==False):
        my_qb_players.append(player)

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

def get_QB_week_stats(player: str, week: int):
    p = league.player_info(name=player)
    stats = p.stats.get(week, "Not available")
    return{
        f"Week {week} Passing Attempts": stats['breakdown'].get('passingAttempts',0),
        f"Week {week} Passing Completions": stats['breakdown'].get('passingCompletions',0),
        f"Week {week} Passing Completion Percentage": stats['breakdown'].get('passingCompletionPercentage',0),
        f"Week {week} Passing Yards": stats['breakdown'].get('passingYards', 0),
        f"Week {week} Passing Touchdowns": stats['breakdown'].get('passingTouchdowns',0),
        f"Week {week} Passing 2 Point Conversions": stats['breakdown'].get('passing2PtConversions' ,0),
        f"Week {week} Rushing 2 Point Conversions": stats['breakdown'].get('rushing2PtConversions' ,0),
        f"Week {week} Passing Interceptions": stats['breakdown'].get('passingInterceptions' ,0),
        f"Week {week} Times Sacked Passing": stats['breakdown'].get('passingTimesSacked' ,0),
        f"Week {week} Passing Fumbles": stats['breakdown'].get('65' ,0),
        f"Week {week} Turnovers": stats['breakdown'].get('turnovers' ,0),
        f"Week {week} Passing First Downs": stats['breakdown'].get('211' ,0),
        f"Week {week} Rush Attempts": stats['breakdown'].get('rushingAttempts' ,0),
        f"Week {week} Rushing Yards": stats['breakdown'].get('rushingYards', 0),
        f"Week {week} Rushing Touchdowns": stats['breakdown'].get('rushingTouchdowns' ,0),
        f"Week {week} Rushing Yards Per Attempt": stats['breakdown'].get('rushingYardsPerAttempt' ,0),
    }        
    
print(get_QB_aggregate_stats("Josh Allen"))   