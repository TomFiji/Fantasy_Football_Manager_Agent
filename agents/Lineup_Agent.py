from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_recent_performance, get_player_list_info, post_week_stats, get_aggregate_stats, get_average_stats, search_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from supabase_client import supabase
sys.path.append(os.path.join(os.path.dirname(__file__), './positional_agents/'))
from positional_agents.WR_Agent import wr_agent, wr_runner
from positional_agents.RB_Agent import rb_agent, rb_runner
from positional_agents.TE_Agent import te_agent, te_runner
from positional_agents.QB_Agent import qb_agent, qb_runner

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

wr_list = get_player_list_info('WR')
rb_list = get_player_list_info('RB')
te_list = get_player_list_info('TE')
qb_list = get_player_list_info('QB')
all_players = wr_list + rb_list + te_list + qb_list
for player in all_players:
    """Pre-cache stats for all positions to speed up analysis"""
    print("📥 Caching player stats for all positions...")
    post_week_stats(player, player['position'])
    
    