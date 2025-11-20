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


def get_RB_aggregate_stats(player: str):
    p = league.player_info(name=player)
    stats = p.stats.get(0, "Not available")
    return{
        "Season Total Rushing Attempts": stats['breakdown'].get('rushingAttempts',0),
        "Season Average Rushing Yards Per Attempt": stats['breakdown'].get('rushingYardsPerAttempt',0),
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
    
print(get_RB_aggregate_stats("Josh Jacobs"))    