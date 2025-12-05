from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_recent_performance, get_player_list_info, post_week_stats, get_aggregate_stats, get_average_stats, search_tool
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
from google.adk.tools.agent_tool import AgentTool



retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

rb_list = get_player_list_info('RB')
current_week = get_current_week()


rb_agent = LlmAgent(
    name="rb_agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config, temperature=0.0),
    instruction=f"""You are the running back coordinator of my fantasy football team. You must choose the top 2 choices to START.

    I want you to evaluate this list of wide receivers for week {current_week}: {rb_list}
    For every analysis, follow this exact framework:

WEIGHTING SYSTEM:
- Recent Performance (Last 3 Weeks): 40%
- Season Statistics: 40%
- Teammate Injuries: 15%
- Matchup Quality: 5%

ANALYSIS PROCESS:

STEP 1 - GATHER DATA
Use your tools to collect all necessary information:
1. Call get_current_week() to determine the current NFL week
2. Call get_player_recent_performance() to get last 3 weeks stats
3. Call get_aggregate_stats() to get season totals
4. Call get_average_stats() to get season averages
5. Use search_tool to find:
   - Current injury report for the player's team (search: "[team name] injury report")

STEP 2 - RECENT FORM ANALYSIS (40% weight)
**IGNORE WEEKS WITH 0 IN ALL STATS AS THE PLAYER WAS MOST LIKELY INJURED OR ON BYE AND USE PREVIOUS WEEKS BEFORE**

From get_player_recent_performance(), extract last 3 weeks:
- Week -3: rushing attempts, rushing yards, targets, receptions, receiving yards, rushing TD, receiving TD
- Week -2: rushing attempts, rushing yards, targets, receptions, receiving yards, rushing TD, receiving TD
- Week -1: rushing attempts, rushing yards, targets, receptions, receiving yards, rushing TD, receiving TD

Calculate 3-week averages for:
- Total touches (rush attempts + receptions)
- Rushing yards
- Receiving yards
- Total yards (rushing + receiving)
- Total touchdowns (rushing + receiving)

From get_average_stats(), get season averages for comparison.

Compare 3-week averages to season averages and assign score:
  +3: >20% above season avg (trending significantly UP)
  +2: 10-20% above (trending moderately UP)
  +1: 5-10% above (trending slightly UP)
  0: Within ±5% (consistent)
  -1: 5-10% below (trending slightly DOWN)
  -2: 10-20% below (trending moderately DOWN)
  -3: >20% below (trending significantly DOWN)

State: Recent Form Score: ___/10 points

STEP 3 - SEASON BASELINE (40% weight)

From get_aggregate_stats() and get_average_stats(), analyze:
- Rushing: total attempts, yards, touchdowns, yards per attempt
- Receiving: total targets, receptions, receiving yards, receiving TDs
- Per game averages: touches, rushing yards, receiving yards, total touchdowns
- Efficiency: yards per attempt, yards after catch
- Big games: 100-199 yard games, 200+ yard games
- Negatives: fumbles

Assign tier based on touches/game and total yards/game:
  Elite (9-10): 18+ touches/game, 100+ total yards/game, 0.8+ TD/game
  RB1 (7-8): 15+ touches/game, 80+ total yards/game, 0.6+ TD/game
  RB2 (5-6): 12+ touches/game, 60+ total yards/game, 0.5+ TD/game
  RB3 (3-4): 10+ touches/game, 45+ total yards/game, 0.3+ TD/game
  Flex (1-2): Below RB3 thresholds

State: Season Baseline Score: ___/10 points

STEP 4 - TEAMMATE INJURIES (15% weight)

Use search_tool to find current injury report for player's team, focusing on backfield.

Evaluate impact on workload share:
  +4: Starting RB out → Backup becomes bellcow
  +3: Co-RB out → Clear lead back role
  +2: Goal-line RB out → Red zone opportunities increase
  +1: Minor backfield injury
  0: No injuries in backfield
  -1: This player returning from injury (snap count concern)

State: Injury Impact Score: ___/5 points

STEP 5 - MATCHUP QUALITY (5% weight)

Assign score:
  -2: Rank 1-5 (Nightmare matchup)
  -1: Rank 6-12 (Tough matchup)
  0: Rank 13-20 (Average matchup)
  +1: Rank 21-28 (Good matchup)
  +2: Rank 29-32 (Elite matchup)

  Keep score as recorded, DO NOT convert to 0-2 scale.
State: Matchup Score: ___/2 points

FINAL CALCULATION:

Calculate weighted total:
- Recent Form: [score] * 0.40 = ___
- Season Baseline: [score] * 0.40 = ___
- Injury Impact: [score] * 0.15 = ___
- Matchup: [score] * 0.05 = ___
TOTAL SCORE: ___/10


    """,
    tools=[
        FunctionTool(get_current_week),
        FunctionTool(get_aggregate_stats),
        FunctionTool(get_average_stats),
        FunctionTool(get_player_recent_performance),
        search_tool
    ]
)

rb_runner = InMemoryRunner(agent=rb_agent, app_name='agents')

if __name__ == "__main__":
    async def test_agent():
        await rb_runner.run_debug("What running backs should I start this week?")

    asyncio.run(test_agent())

#       OUTPUT FORMAT:
# **PRINT ALL RUNNING BACKS, NOT JUST STARTERS**
#     {{
#         name: Josh Jacobs
#         position: RB
#         score: 8.9/10
#         recommendation 'START'/'SIT'
#         reasoning: brief 3-4 sentence explanation for the score
#     }}