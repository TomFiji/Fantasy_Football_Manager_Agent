from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league
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

my_wr_players = []
for player in my_lineup:
    if (player.position == 'WR' and player.on_bye_week==False):
        my_wr_players.append({"name": player.name, "player_id": player.playerId, "Opposing team": player.pro_opponent, "Opposing team's defensive rank against WRs": player.pro_pos_rank})


def get_WR_aggregate_stats(player_id: int):
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

def get_WR_average_stats(player_id: int):
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
    
def get_WR_week_stats(player_id: int, player_name: str, week: int):
    p = league.player_info(playerId=player_id)
    stats = p.stats.get(week, "Not available")
    if (stats == "Not available"): 
        data = f"Week {week}: Didn't play because they were benched or on BYE week."
    else:
        data = {
            f"Week {week} Receptions": stats['breakdown'].get('receivingReceptions',0),
            f"Week {week} Targets": stats['breakdown'].get('receivingTargets', 0),
            f"Week {week} Receiving Yards": stats['breakdown'].get('receivingYards', 0),
            f"Week {week} Touchdowns": stats['breakdown'].get('receivingTouchdowns', 0),
            f"Week {week} Yards After Catch": stats['breakdown'].get('receivingYardsAfterCatch', 0),
            f"Week {week} Targets": stats['breakdown'].get('receivingTargets', 0),
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
        .insert({"player_id": id, "week": week, "player_name": player_name, "stats_breakdown": data, "points": stats.get('points', 0)})
        .execute()
    )
    return response  
    
def get_all_stats(player):
    print(get_WR_aggregate_stats(player.name))
    print(get_WR_average_stats(player.name))
    print(get_WR_week_stats(player.name, player.id, league.current_week-1))

def get_player_weekly_stats(player_id: int, week: int):
    response = (
        supabase.table("player_weekly_stats")
        .select("*")
        .eq("player_id", player_id)
        .eq("week", week)
        .execute()
    )
    if (response.data==[]):
        print("Nothing to show here")
        return None
    else:
        return response.data[0]['player_name'] 

#print(get_WR_week_stats(4258173, "Nico Collins", 10))    
print(my_wr_players)

             
