from dotenv import load_dotenv
import os
from espn_api.football import League

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

API_KEY = os.environ['GOOGLE_API_KEY']
LEAGUE_ID = os.environ['ESPN_LEAGUE_ID']
YEAR = 2025
ESPN_S2 = os.environ['ESPN_S2_COOKIE']
SWID = os.environ['ESPN_SWID_COOKIE']
MY_TEAM_ID = os.environ['MY_TEAM_ID']

league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)

my_team = league.teams[int(MY_TEAM_ID)-1]
p = league.player_info(playerId=4258173)
stats = p.stats.get(11, "Not available")
#print(stats)
for player in my_team.roster:
    pass
    #print(f"Name: {player.name}, ID: {player.playerId}")
    #print(f"Name: {player.name} Status: {player.active_status}")
# for player in my_team.roster:
#     if (player.name == 'Nico Collins'):
#         print(f"Name: {player.name}, Stats: {player.stats}")

#{'Player was on bye' if player.active_status == 'bye' else player.stats[11]['points']}    