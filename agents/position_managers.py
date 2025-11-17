from dotenv import load_dotenv
import os
import asyncio
import base64

load_dotenv()

API_KEY = os.environ['GOOGLE_API_KEY']
LEAGUE_ID = os.environ['ESPN_LEAGUE_ID']
YEAR = 2025
ESPN_S2 = os.environ['ESPN_S2_COOKIE']
SWID = os.environ['ESPN_SWID_COOKIE']
MY_TEAM_ID = os.environ['MY_TEAM_ID']


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
