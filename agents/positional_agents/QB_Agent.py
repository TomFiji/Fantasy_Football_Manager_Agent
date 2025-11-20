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
    
print(get_QB_aggregate_stats("Josh Allen"))   