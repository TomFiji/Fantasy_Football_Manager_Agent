from dotenv import load_dotenv
import os
import sys
import asyncio
import base64
import math
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.espn_client import my_team, league
from utils.shared_tools import get_current_week, get_player_recent_performance, get_player_list_info, post_week_stats, get_aggregate_stats, get_average_stats, search_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from supabase_client import supabase
sys.path.append(os.path.join(os.path.dirname(__file__), './positional_agents/'))
from positional_agents.WR_Agent import wr_agent, wr_runner, wr_list
from positional_agents.RB_Agent import rb_agent, rb_runner, rb_list
from positional_agents.TE_Agent import te_agent, te_runner, te_list
from positional_agents.QB_Agent import qb_agent, qb_runner, qb_list

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

# logging.basicConfig(level=logging.WARNING, stream=sys.stdout, 
#                     format='%(levelname)s: %(message)s')

USER_ID = "fantasy_mgr_user"


# all_players = wr_list + rb_list + te_list + qb_list
# print("📥 Caching player stats for all positions...")
# for player in all_players:
#     """Pre-cache stats for all positions to speed up analysis"""
#     post_week_stats(player, player['position'])
    
async def run_agent_query(runner, query: str, user_id: str, session_id: str) -> str:
    """
    Guarantees the session exists or is created before running the agent.
    """
    
    # 1. Ensure the session exists (using runner's internal session_service)
    try:
        session = runner.session_service.get_session(
            app_name='agents', 
            user_id=user_id, 
            session_id=session_id
        )
    except ValueError:
        # Session not found: CREATE it
        session = runner.session_service.create_session(
            app_name='agents', 
            user_id=user_id, 
            session_id=session_id
        )
        
    # 2. Run the agent using the guaranteed session object
    new_message_content = types.Content(role='user', parts=[types.Part(text=query)])
    
    # You would then call a low-level method using the session object
    # The exact method here is dependent on your ADK version.
    
    # This is often the correct method, where the session is passed as an argument:
    final_response_text = ""
    
    # --- FIX 3: Revert the runner call to only use IDs ---
    # The session object is NOT passed here.
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message_content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response_text = event.content.parts[0].text
            break 

    return final_response_text   
    
async def analyze_positions():
    """Run all position agents and collect their rankings"""
    print("🏈 Analyzing positions...\n")
    
    wr_session_id = str(uuid.uuid4())
    rb_session_id = str(uuid.uuid4())
    te_session_id = str(uuid.uuid4())
    
    # Create tasks WITHOUT await
    print("Creating WR task...")
    wr_task = run_agent_query(
        runner=wr_runner, 
        query="Rank all WRs with detailed grades and reasoning",
        user_id=USER_ID,
        session_id=wr_session_id
        )
    
    print("Creating RB task...")
    rb_task = run_agent_query(
        runner=rb_runner,
        query="Rank all RBs with detailed grades and reasoning",
        user_id=USER_ID,
        session_id=rb_session_id
        )
    
    print("Creating TE task...")
    te_task = run_agent_query(
        runner=te_runner,
        query="Rank all TEs with detailed grades and reasoning",
        user_id=USER_ID,
        session_id=te_session_id
        )
    
    print("Waiting for all tasks to complete...")
    # Wait for all to complete
    try:
        wr_result, rb_result, te_result = await asyncio.gather(wr_task, rb_task, te_task)
    except Exception as e:
        print(f"An error occurred during concurrent agent execution: {e}")
        # Handle exceptions appropriately, perhaps by returning an error message
        return {'error': str(e)}
    
    print("All tasks completed!\n")
    
    result = {
        'wr': wr_result,
        'rb': rb_result,
        'te': te_result
    }
    
    return result
    
if __name__ == "__main__":
    result = asyncio.run(analyze_positions())
    
    print("\n" + "="*60)
    print("WR RANKINGS:")
    print("="*60)
    print(result['wr'])
    
    print("\n" + "="*60)
    print("RB RANKINGS:")
    print("="*60)
    print(result['rb'])
    
    print("\n" + "="*60)
    print("TE RANKINGS:")
    print("="*60)
    print(result['te'])