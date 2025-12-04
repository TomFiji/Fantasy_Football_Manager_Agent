from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
import logging
import json
from io import StringIO
from contextlib import redirect_stdout
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_recent_performance, get_player_list_info, post_week_stats, get_aggregate_stats, get_average_stats, search_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from supabase_client import supabase
sys.path.append(os.path.join(os.path.dirname(__file__), './positional_agents/'))
from positional_agents.WR_Agent import wr_agent, wr_list
from positional_agents.RB_Agent import rb_agent, rb_list
from positional_agents.TE_Agent import te_agent, te_list
from positional_agents.QB_Agent import qb_agent, qb_list

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
from google.genai.types import Part, Content

from google.adk.apps.app import App, ResumabilityConfig
from google.adk.tools.function_tool import FunctionTool
from google.adk.runners import InMemoryRunner

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
#                     format='%(levelname)s: %(message)s')

# TEST MODE - Set to True to use hardcoded data instead of running agents

USER_ID = "fantasy_mgr_user"


# Create individual runners for each agent (no LoopAgent needed - agents complete in one turn)
wr_runner = InMemoryRunner(agent=wr_agent, app_name='agents')
rb_runner = InMemoryRunner(agent=rb_agent, app_name='agents')
te_runner = InMemoryRunner(agent=te_agent, app_name='agents')
qb_runner = InMemoryRunner(agent=qb_agent, app_name='agents')


# Test data for development/debugging

# all_players = wr_list + rb_list + te_list + qb_list
# print("📥 Caching player stats for all positions...")
# for player in all_players:
#     """Pre-cache stats for all positions to speed up analysis"""
#     post_week_stats(player, player['position'])
    

# Create coordinator agent (no tools needed - just parses text)
coordinator_agent = LlmAgent(
    name="lineup_coordinator",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""You are the lineup coordinator.

You will receive text analysis from position agents (WR, RB, TE, QB).

Your job: Extract which players they recommended to START vs SIT.
Put the top 3 players with recommendation: SIT into flex_candidate list based on their player_grade

Output ONLY valid JSON:
{
    "wr_starters": ['Player Name 1: Reasoning', 'Player Name 2: Reasoning'],
    "rb_starters": ['Player Name 1: Reasoning', 'Player Name 2: Reasoning'],
    "te_starters": ['Player Name 1: Reasoning'],
    "qb_starters": ['Player Name 1: Reasoning']
    "flex_candidate":['Player Name 1: Reasoning', 'Player Name 2: Reasoning', 'Player Name 3: Reasoning']
}

Rules:
- Extract exact player names from the text
- starters = players recommended to START
- flex_candidates = players recommended to SIT
- Do not add analysis or reasoning, just the JSON
""",
    tools=[]  # ← NO TOOLS! Just text parsing
)

coordinator_runner = InMemoryRunner(agent=coordinator_agent, app_name='agents')


async def analyze_positions():
    """Step 1: Run all position agents"""
    print("🏈 Analyzing positions...\n")
    
    wr_result = await wr_runner.run_debug("What wide receivers should I start?")
    await asyncio.sleep(30)
    rb_result = await rb_runner.run_debug("What running backs should I start?")
    await asyncio.sleep(30)
    te_result = await te_runner.run_debug("What tight end should I start?")
    await asyncio.sleep(30)
    qb_result = await qb_runner.run_debug("What quarterback should I start?")
    await asyncio.sleep(30)
    
    
    return {
        'wr': wr_result,
        'rb': rb_result,
        'te': te_result,
        'qb': qb_result
    }


async def extract_lineup_decisions(position_results):
    """Step 2: Use coordinator to extract structured decisions"""
    print("📋 Extracting lineup decisions...\n")
    
    # Combine all position agent outputs into one prompt
    combined_prompt = f"""
Extract START and SIT recommendations from these position agent analyses:

===== WR AGENT OUTPUT =====
{position_results['wr']}

===== RB AGENT OUTPUT =====
{position_results['rb']}

===== TE AGENT OUTPUT =====
{position_results['te']}

===== QB AGENT OUTPUT =====
{position_results['qb']}

Extract the player names and output the JSON.
"""
    
    # Call coordinator agent
    lineup_json = await coordinator_runner.run_debug(combined_prompt)
    
    # Parse JSON
    try:
        # Strip markdown if present
        if "```json" in lineup_json:
            lineup_json = lineup_json.split("```json")[1].split("```")[0].strip()
        elif "```" in lineup_json:
            lineup_json = lineup_json.split("```")[1].split("```")[0].strip()
        
        lineup_data = json.loads(lineup_json)
        return lineup_data
    except Exception as e:
        print(f"❌ Failed to parse coordinator output: {e}")
        print("Raw output:")
        print(lineup_json)
        return None


async def analyze_full_lineup():
    """Main orchestrator"""
    print("\n" + "="*60)
    print("🏈 FANTASY FOOTBALL LINEUP ANALYZER")
    print("="*60 + "\n")
    
    # Step 1: Run position agents
    position_results = await analyze_positions()
    
    # Step 2: Extract structured decisions
    lineup_decisions = await extract_lineup_decisions(position_results)
    
    if lineup_decisions:
        print("\n" + "="*60)
        print("STARTING LINEUP")
        print("="*60)
        print(f"WR: {', '.join(lineup_decisions.get('wr_starters', []))}")
        print(f"RB: {', '.join(lineup_decisions.get('rb_starters', []))}")
        print(f"TE: {', '.join(lineup_decisions.get('te_starters', []))}")
        print(f"QB: {', '.join(lineup_decisions.get('qb_starters', []))}")
        
        print("\n" + "="*60)
        print("FLEX CANDIDATES")
        print("="*60)
        print(f"FLEX: {', '.join(lineup_decisions.get('flex_candidates', []))}")
        print("="*60 + "\n")
    
    return lineup_decisions


if __name__ == "__main__":
    result = asyncio.run(analyze_full_lineup())

















#TO DO LIST TOMORROW
# 1. Implement QB into analyze_stats
# 2. Take all the starts from each JSON and add to a starting_squad list
# 3. Create flex agent to analyze all SIT candidates
# 4. Flex agent needs to pick one option and add it to starting_squad list
# 5. Look into AI agent consistency for each position
