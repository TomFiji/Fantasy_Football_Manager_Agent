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
current_week = get_current_week()


qb_agent = LlmAgent(
    name="qb_agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config, temperature=0.0),
    instruction=f"""You are the quarterback coordinator of my fantasy football team. Your goal is to choose the one best option.
    Analyze the list {qb_list} for week {current_week}
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
   - Current injury report for the player's team (search: "[team name] injury report wide receivers tight ends")
   - Offensive line injury status (search: "[team name] offensive line injury report")

STEP 2 - RECENT FORM ANALYSIS (40% weight)
**IGNORE WEEKS WITH 0 IN ALL STATS AS THE PLAYER WAS MOST LIKELY INJURED OR ON BYE AND USE PREVIOUS WEEKS BEFORE**

From get_player_recent_performance(), extract last 3 weeks:
- Week -3: passing attempts, completions, passing yards, passing TD, interceptions, rushing attempts, rushing yards, rushing TD, sacks, turnovers
- Week -2: passing attempts, completions, passing yards, passing TD, interceptions, rushing attempts, rushing yards, rushing TD, sacks, turnovers
- Week -1: passing attempts, completions, passing yards, passing TD, interceptions, rushing attempts, rushing yards, rushing TD, sacks, turnovers

Calculate 3-week averages for:
- Passing attempts
- Passing yards
- Passing touchdowns
- Interceptions
- Rushing yards
- Total touchdowns (passing + rushing)
- Turnovers
- Completion percentage

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
- Passing: total attempts, completions, completion percentage, yards, touchdowns, interceptions
- Rushing: total attempts, yards, touchdowns, yards per attempt
- Per game averages: attempts, passing yards, passing TD, interceptions, rushing yards
- Efficiency: completion percentage, first downs per game
- Negatives: sacks, turnovers, fumbles
- Big games: 300-399 yard games, 400+ yard games
- Milestone bonuses: completion milestones (every 5, every 10)

Assign tier based on attempts/game and passing yards/game:
  Elite (9-10): 35+ attempts/game, 280+ pass yards/game, 2.0+ pass TD/game
  QB1 (7-8): 30+ attempts/game, 240+ pass yards/game, 1.5+ pass TD/game
  QB2 (5-6): 28+ attempts/game, 220+ pass yards/game, 1.2+ pass TD/game
  Streaming (3-4): 25+ attempts/game, 200+ pass yards/game, 1.0+ pass TD/game
  Bench (1-2): Below streaming thresholds

State: Season Baseline Score: ___/10 points

STEP 4 - TEAMMATE INJURIES (15% weight)

Use search_tool to find current injury report for player's team, focusing on pass catchers and offensive line.

Evaluate impact on passing game and protection (NOTE: For QBs, healthy weapons = positive score):
  +4: WR1 + WR2 healthy, elite weapons available, strong O-line
  +3: Primary receiving weapons healthy (WR1, WR2, TE1 all active)
  +2: Key WR or TE returning from injury this week
  +1: TE1 or RB1 healthy (checkdown/safety valve options)
  0: Average weapons situation, some injuries
  -1: WR1 or WR2 out
  -2: Multiple key pass catchers out (2+ of WR1/WR2/TE1)
  -3: Multiple O-line injuries causing pressure/sack concerns

  Keep score as recorded, DO NOT convert to 0-3 scale.

State: Injury Impact Score: ___/5 points

STEP 5 - MATCHUP QUALITY (5% weight)


Assign score:
  -2: Rank 1-5 (Nightmare matchup)
  -1: Rank 6-12 (Tough matchup)
  0: Rank 13-20 (Average matchup)
  +1: Rank 21-28 (Good matchup)
  +2: Rank 29-32 (Nightmare matchup)

State: Matchup Score: ___/2 points

FINAL CALCULATION:

Calculate weighted total:
- Recent Form: [score] * 0.40 = ___
- Season Baseline: [score] * 0.40 = ___
- Injury Impact: [score] * 0.15 = ___
- Matchup: [score] * 0.05 = ___
TOTAL SCORE: ___/10

OUTPUT FORMAT:
**PRINT ALL QUARTERBACKS, NOT JUST STARTERS**
    {{
        name: Drake Maye
        position: QB
        score: 8.9/10
        recommendation 'START'/'SIT'
        reasoning: brief 3-4 sentence explanation for the score
    }}
    
    """,
    tools=[
        FunctionTool(get_current_week),
        FunctionTool(get_aggregate_stats),
        FunctionTool(get_average_stats),
        FunctionTool(get_player_recent_performance),
        search_tool
    ]
)

qb_runner = InMemoryRunner(agent=qb_agent, app_name='agents')

if __name__ == "__main__":
    async def test_agent():
        response = await qb_runner.run_debug("What quarterbacks should I start this week?")

    asyncio.run(test_agent())     