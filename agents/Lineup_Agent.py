from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
import logging
import json
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

from google.adk.agents import LlmAgent, LoopAgent
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

# logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
#                     format='%(levelname)s: %(message)s')

# TEST MODE - Set to True to use hardcoded data instead of running agents
TEST_MODE = False

USER_ID = "fantasy_mgr_user"


wr_agent_limited = LoopAgent(
    name="wr_agent_limited",
    sub_agents=[wr_agent], # The agent we want to run
    max_iterations=10           # <--- Sets the hard limit for turns/calls
)
rb_agent_limited = LoopAgent(
    name="rb_agent_limited",
    sub_agents=[rb_agent], # The agent we want to run
    max_iterations=10           # <--- Sets the hard limit for turns/calls
)
te_agent_limited = LoopAgent(
    name="te_agent_limited",
    sub_agents=[te_agent], # The agent we want to run
    max_iterations=10           # <--- Sets the hard limit for turns/calls
)
qb_agent_limited = LoopAgent(
    name="qb_agent_limited",
    sub_agents=[qb_agent], # The agent we want to run
    max_iterations=10           # <--- Sets the hard limit for turns/calls
)

# Create individual runners for each agent
wr_runner = InMemoryRunner(agent=wr_agent_limited, app_name='agents')
rb_runner = InMemoryRunner(agent=rb_agent_limited, app_name='agents')
te_runner = InMemoryRunner(agent=te_agent_limited, app_name='agents')
qb_runner = InMemoryRunner(agent=qb_agent_limited, app_name='agents')


# Test data for development/debugging
TEST_DATA = {
    'wr': [
        {
            "rank": 1,
            "player_name": "Michael Wilson",
            "player_id": "4360761",
            "player_grade": 88,
            "recommendation": "START",
            "opponent": "LAR",
            "opponent ranking against WR": 19,
            "reasoning": "Wilson is poised for a significant increase in usage with star receiver Marvin Harrison Jr. battling a heel injury."
        },
        {
            "rank": 2,
            "player_name": "Nico Collins",
            "player_id": "4258173",
            "player_grade": 85,
            "recommendation": "START",
            "opponent": "KC",
            "opponent ranking against WR": 5,
            "reasoning": "Collins is a consistent, high-volume receiver, averaging over 8 targets and 72 yards per game."
        },
        {
            "rank": 3,
            "player_name": "Chris Godwin Jr.",
            "player_id": "3116165",
            "player_grade": 75,
            "recommendation": "SIT",
            "opponent": "NO",
            "opponent ranking against WR": 17,
            "reasoning": "Godwin is trending in the right direction but not yet back to a full snap count."
        }
    ],
    'rb': [
        {
            "rank": 1,
            "player_name": "Christian McCaffrey",
            "player_id": "3116385",
            "player_grade": 95,
            "recommendation": "START",
            "opponent": "BUF",
            "opponent ranking against RB": 12,
            "reasoning": "Elite talent with consistent volume and usage."
        },
        {
            "rank": 2,
            "player_name": "Tony Pollard",
            "player_id": "3929630",
            "player_grade": 70,
            "recommendation": "SIT",
            "opponent": "WSH",
            "opponent ranking against RB": 8,
            "reasoning": "Tough matchup against strong run defense."
        }
    ],
    'te': [
        {
            "rank": 1,
            "player_name": "Travis Kelce",
            "player_id": "2977644",
            "player_grade": 90,
            "recommendation": "START",
            "opponent": "HOU",
            "opponent ranking against TE": 15,
            "reasoning": "Top target in high-powered offense."
        },
        {
            "rank": 2,
            "player_name": "Dallas Goedert",
            "player_id": "3116389",
            "player_grade": 65,
            "recommendation": "SIT",
            "opponent": "CAR",
            "opponent ranking against TE": 10,
            "reasoning": "Inconsistent target share in struggling offense."
        }
    ],
    'qb': [
        {
            "rank": 1,
            "player_name": "Josh Allen",
            "player_id": "3115942",
            "player_grade": 92,
            "recommendation": "START",
            "opponent": "SF",
            "opponent ranking against QB": 14,
            "reasoning": "Dual-threat QB with elite rushing floor."
        }
    ]
}

starting_lineup = []
flex_candidates = []

# all_players = wr_list + rb_list + te_list + qb_list
# print("📥 Caching player stats for all positions...")
# for player in all_players:
#     """Pre-cache stats for all positions to speed up analysis"""
#     post_week_stats(player, player['position'])
    
async def run_agent_query(runner, query: str, user_id: str, session_id: str) -> str:
    """
    Run agent query using run_debug which handles sessions automatically.
    """
    events = await runner.run_debug(
        user_messages=query,
        session_id=session_id,
        quiet=True
    )

    # Extract the final response from events
    for event in reversed(events):
        if event.is_final_response() and event.content and event.content.parts:
            return event.content.parts[0].text

    return ""   
    
async def analyze_positions():
    """Run all position agents and collect their rankings"""
    print("🏈 Analyzing positions...\n")

    # Generate unique session IDs for each task
    wr_session_id = str(uuid.uuid4())
    rb_session_id = str(uuid.uuid4())
    te_session_id = str(uuid.uuid4())
    qb_session_id = str(uuid.uuid4())

    # --- WR TASK ---
    print("🚀 Starting WR analysis...")
    # Run sequentially. The time this takes (e.g. 5-10s) acts as a natural buffer.
    wr_result = await run_agent_query(
        runner=wr_runner,
        query="Rank all WRs with detailed grades and reasoning. I need to START exactly 2 WRs. Mark the top 2 as 'START' and the rest as 'SIT'.",
        user_id=USER_ID,
        session_id=wr_session_id
    )
    print("✅ WR Task Complete.")
    await asyncio.sleep(30)
    # No sleep needed here for Flash usually, unless your agents are extremely fast.

    # --- RB TASK ---
    print("🚀 Starting RB analysis...")
    rb_result = await run_agent_query(
        runner=rb_runner,
        query="Rank all RBs with detailed grades and reasoning. I need to START exactly 2 RBs. Mark the top 2 as 'START' and the rest as 'SIT'.",
        user_id=USER_ID,
        session_id=rb_session_id
    )
    print("✅ RB Task Complete.")
    await asyncio.sleep(30)

    # --- TE TASK ---
    print("🚀 Starting TE analysis...")
    te_result = await run_agent_query(
        runner=te_runner,
        query="Rank all TEs with detailed grades and reasoning. I need to START exactly 1 TE. Mark the top 1 as 'START' and the rest as 'SIT'.",
        user_id=USER_ID,
        session_id=te_session_id
    )
    print("✅ TE Task Complete.")
    await asyncio.sleep(30)

    # --- QB TASK ---
    print("🚀 Starting QB analysis...")
    qb_result = await run_agent_query(
        runner=qb_runner,
        query="Rank all QBs with detailed grades and reasoning. I need to START exactly 1 QB. Mark the top 1 as 'START' and the rest as 'SIT'. Note: I must start a QB even if the matchup is difficult.",
        user_id=USER_ID,
        session_id=qb_session_id
    )
    print("✅ QB Task Complete.")
    await asyncio.sleep(30)
    
    
    
    return {
        'wr': wr_result,
        'rb': rb_result,
        'te': te_result,
        'qb': qb_result
    }
    
    
if __name__ == "__main__":
    if TEST_MODE:
        print("🧪 Running in TEST MODE with hardcoded data\n")
        result = TEST_DATA
    else:
        print("🚀 Running agents to analyze positions...\n")
        result = asyncio.run(analyze_positions())

    # Process results
    for position_name, position_data in result.items():
        print(f"Processing {position_name.upper()}...")

        # If position_data is a string (from agent), parse it as JSON
        if isinstance(position_data, str):
            try:
                # Strip markdown code fences if present (defensive programming)
                cleaned_data = position_data.strip()
                if cleaned_data.startswith('```'):
                    # Remove opening fence (```json or ```)
                    lines = cleaned_data.split('\n')
                    lines = lines[1:]  # Remove first line with ```json
                    # Remove closing fence
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    cleaned_data = '\n'.join(lines)

                players = json.loads(cleaned_data)
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing {position_name} data: {e}")
                print(f"Raw data: {position_data[:200]}...")
                continue
        # If it's already a list (from TEST_DATA), use it directly
        elif isinstance(position_data, list):
            players = position_data
        else:
            print(f"❌ Unexpected data type for {position_name}: {type(position_data)}")
            continue

        # Sort players into starting lineup or flex candidates
        for player in players:
            if player['recommendation'] == 'START':
                starting_lineup.append(player)
            else:
                flex_candidates.append(player)

        print(f"✅ Processed {len(players)} {position_name.upper()} players\n")

    print("=" * 50)
    print("-------STARTING LINEUP---------")
    print(json.dumps(starting_lineup, indent=2))
    print("\n-------FLEX CANDIDATES---------")
    print(json.dumps(flex_candidates, indent=2))
    print("=" * 50)
    
    print(result)
#TO DO LIST TOMORROW
# 1. Implement QB into analyze_stats
# 2. Take all the starts from each JSON and add to a starting_squad list
# 3. Create flex agent to analyze all SIT candidates
# 4. Flex agent needs to pick one option and add it to starting_squad list
# 5. Look into AI agent consistency for each position
