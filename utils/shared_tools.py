import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from supabase_client import supabase
from googlesearch import search
from utils.espn_client import my_team, league
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from google.adk.tools.google_search_tool import GoogleSearchTool



def get_current_week() -> int:
    return league.current_week

box_scores = league.box_scores(get_current_week())
for matchup in box_scores:
    if matchup.home_team == my_team or matchup.away_team == my_team:
        my_lineup = matchup.home_lineup if matchup.home_team == my_team else matchup.away_lineup



def get_player_list_info(position) -> list[dict]:
    my_players = []
    for player in my_lineup:
        if (player.position == position and player.on_bye_week==False):
            my_players.append({"player_name": player.name, "player_id": player.playerId, "position": player.position, "team": player.proTeam, "opponent": player.pro_opponent, f"opponent_rank_against_{position}s": player.pro_pos_rank, "injury_status": player.injuryStatus})
    return my_players

search_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='SearchAgent',
    instruction='You are a specialist in Google Search grounding. Use web search to find current, factual information and provide structured, well organized findings.',
    tools=[GoogleSearchTool()]
)

search_tool = AgentTool(agent=search_agent)

def get_aggregate_stats(player_id: int, position: str) -> dict:
    p = league.player_info(playerId=player_id)
    stats = p.stats.get(0, "Not available")
    if (stats=="Not available"):
        return "Player has not played yet"
    else:
        aggregate_data = {}
        breakdown = stats['breakdown']
        points = stats['points']
        games_played = breakdown.get('210', 0)
        STATS_NEEDING_GAME_MULTIPLIER = ['receivingYards', 'rushingYards', 'passingYards']
        for display_name, stat_key in POSITION_STATS[position]:
            if stat_key in STATS_NEEDING_GAME_MULTIPLIER:
                aggregate_data[f"Season Total {display_name}"] = math.ceil(breakdown.get(stat_key, 0)*games_played)
            else:    
                aggregate_data[f"Season Total {display_name}"] = breakdown.get(stat_key, 0)
        if position == 'WR':
            aggregate_data[f"Season Total Touchdowns with 40-49 Yard Reception"] = (
                breakdown.get('receiving40PlusYardTD', 0) - breakdown.get('receiving50PlusYardTD', 0)
            )
            aggregate_data[f"Season Total 100-199 Receving Yard Games"] = breakdown.get('receiving100To199YardGame',0)
            targets = breakdown.get('receivingTargets', 0)
            receptions = breakdown.get('receivingReceptions', 0)
            aggregate_data[f"Season Total Catch Rate Percentage"] = round(
                (receptions / targets) if targets != 0 else 0, 2
            )

            aggregate_data[f"Season Total Fantasy Points Per Target"] = round(
                (points / targets) if targets != 0 else 0, 2
            )
    
        elif position == 'RB':
            aggregate_data[f"Season Total Touchdowns with 40-49 Yards Rushing"] = (
                breakdown.get('rushing40PlusYardTD', 0) - breakdown.get('rushing50PlusYardTD', 0)
            )
        
        elif position == 'TE':
            targets = breakdown.get('receivingTargets', 0)
            receptions = breakdown.get('receivingReceptions', 0)
            aggregate_data[f"Season Total Catch Rate Percentage"] = round(
                (receptions / targets) if targets != 0 else 0, 2
            )
            
            aggregate_data[f"Season Total Fantasy Points Per Target"] = round(
                (points / targets) if targets != 0 else 0, 2
            )
        return aggregate_data          

def get_average_stats(player_id: int, position: str) -> dict:
    p = league.player_info(playerId=player_id)
    stats = p.stats.get(0, "Not available")
    if (stats=="Not available"):
        return "Player has not played yet"
    else:
        average_data = {}
        breakdown = stats['breakdown']
        points = stats['points']
        games_played = breakdown.get('210', 0)
        STATS_ALREADY_AVERAGED = ['rushingYardsPerAttempt', 'rushingYards', 'receivingYards', 'receivingYardsPerReception', 'passingYards', 'passingCompletionPercentage']
        for display_name, stat_key in AVERAGE_STATS[position]:
            if stat_key in STATS_ALREADY_AVERAGED:
                average_data[f"{display_name}"] = breakdown.get(stat_key, 0)
            else:
                average_data[f"{display_name}"] = round(breakdown.get(stat_key, 0)/games_played, 2)
        if position == 'WR' or 'TE':
            targets = breakdown.get('receivingTargets', 0)
            receptions = breakdown.get('receivingReceptions', 0)
            
            average_data['Season Average Catch Rate Percentage'] = round(
                (receptions / targets) if targets != 0 else 0, 2
            )
        
        elif position == 'QB':
            tds = breakdown.get('passingTouchdowns', 0)
            ints = breakdown.get('passingInterceptions', 0)
            
            average_data['Season Average TD:INT Ratio'] = round(
                (tds / ints) if ints != 0 else tds, 2
            )
        return average_data
    
   
def post_week_stats(player, position: str)-> dict:
    p = league.player_info(playerId=player["player_id"])
    if league.current_week<5:
        week_range = range(1, league.current_week)
    else:
        week_range = range(league.current_week-4, league.current_week)
    for week in week_range:
        response = (
            supabase.table("player_weekly_stats")
            .select("*")  # Just select one column (faster)
            .eq("player_id", player["player_id"])
            .eq("week", week)
            .execute()
        )
        if response.data:
            pass
        else:
            stats = p.stats.get(week, "Not available")
            data = {}
            if (stats == "Not available"): 
                data[f"Week {week} Stats"] = "Didn't play because they were benched or on BYE week."
            else:
                breakdown = stats['breakdown']
                points = stats['points']
                for display_name, stat_key in POSITION_STATS[position]:
                    data[f"Week {week} {display_name}"] = breakdown.get(stat_key, 0)
                if position == 'WR':
                    data[f"Week {week} Touchdowns with 40-49 Yard Reception"] = (
                        breakdown.get('receiving40PlusYardTD', 0) - breakdown.get('receiving50PlusYardTD', 0)
                    )
                    targets = breakdown.get('receivingTargets', 0)
                    receptions = breakdown.get('receivingReceptions', 0)
                    data[f"Week {week} Catch Rate Percentage"] = round(
                        (receptions / targets) if targets != 0 else 0, 2
                    )

                    data[f"Week {week} Fantasy Points Per Target"] = round(
                        (points / targets) if targets != 0 else 0, 2
                    )
                
                elif position == 'RB':
                    data[f"Week {week} Touchdowns with 40-49 Yards Rushing"] = (
                        breakdown.get('rushing40PlusYardTD', 0) - breakdown.get('rushing50PlusYardTD', 0)
                    )
                
                elif position == 'TE':
                    targets = breakdown.get('receivingTargets', 0)
                    receptions = breakdown.get('receivingReceptions', 0)
                    data[f"Week {week} Catch Rate Percentage"] = round(
                        (receptions / targets) if targets != 0 else 0, 2
                    )
                    
                    data[f"Week {week} Fantasy Points Per Target"] = round(
                        (points / targets) if targets != 0 else 0, 2
                    )    
            response = (
                supabase.table("player_weekly_stats")
                .insert({"player_id": player["player_id"], "week": week, "player_name": player["player_name"], "stats_breakdown": data, "points": stats.get('points', 0) if stats != 'Not available' else 0})
                .execute()
            )
            print(f"{player['player_name']} for week {week} added")   

def get_player_recent_performance(player_id: int)-> dict:
    recent_stats = {}
    if get_current_week()<5:
        weeks = range(1, get_current_week())
    else:
        weeks = range(get_current_week()-4, get_current_week())
    for week in weeks:
        response = (
        supabase.table("player_weekly_stats")
        .select("*")
        .eq("player_id", player_id)
        .eq("week", week)
        .execute()
        )
        recent_stats.update(response.data[0]['stats_breakdown'])
    return recent_stats    
            
        
        
                
        
  
POSITION_STATS = {
    'WR': [
        ('Receptions', 'receivingReceptions'),
        ('Targets', 'receivingTargets'),
        ('Receiving Yards', 'receivingYards'),
        ('Touchdowns', 'receivingTouchdowns'),
        ('Yards After Catch', 'receivingYardsAfterCatch'),
        ('First Downs', '213'),
        ('Touchdowns with 0-9 Yard Reception', '183'),
        ('Touchdowns with 10-19 Yard Reception', '184'),
        ('Touchdowns with 20-29 Yard Reception', '185'),
        ('Touchdowns with 30-39 Yard Reception', '186'),
        ('Touchdowns with 50+ Yard Reception', 'receiving50PlusYardTD'),
        ('Every 5 Receptions', '54'),
        ('Every 10 Receptions', '55'),
    ],
    'RB': [
        ('Rushing Attempts', 'rushingAttempts'),
        ('Rushing Yards Per Attempt', 'rushingYardsPerAttempt'),
        ('Receptions', 'receivingReceptions'),
        ('Targets', 'receivingTargets'),
        ('Rushing Yards', 'rushingYards'),
        ('Receiving Touchdowns', 'receivingTouchdowns'),
        ('Rushing Touchdowns', 'rushingTouchdowns'),
        ('Yards After Catch', 'receivingYardsAfterCatch'),
        ('Fumbles', 'fumbles'),
        ('First Downs', '213'),
        ('100-199 Rushing Yard Game', 'rushing100To199YardGame'),
        ('200+ Rushing Yard Game', 'rushing200PlusYardGame'),
        ('Touchdowns with 50+ Yards Rushing', 'rushing50PlusYardTD'),
        ('Every 5 Receptions', '54'),
        ('Every 10 Receptions', '55'),
    ],
    'QB': [
        ('Passing Attempts', 'passingAttempts'),
        ('Passing Completions', 'passingCompletions'),
        ('Passing Completion Percentage', 'passingCompletionPercentage'),
        ('Passing Yards', 'passingYards'),
        ('Passing Touchdowns', 'passingTouchdowns'),
        ('Passing 2 Point Conversions', 'passing2PtConversions'),
        ('Rushing 2 Point Conversions', 'rushing2PtConversions'),
        ('Passing Interceptions', 'passingInterceptions'),
        ('Times Sacked Passing', 'passingTimesSacked'),
        ('Passing Fumbles', '65'),
        ('Turnovers', 'turnovers'),
        ('Passing First Downs', '211'),
        ('Rush Attempts', 'rushingAttempts'),
        ('Rushing Yards', 'rushingYards'),
        ('Rushing Touchdowns', 'rushingTouchdowns'),
        ('Rushing Yards Per Attempt', 'rushingYardsPerAttempt'),
    ],
    'TE': [
        ('Receptions', 'receivingReceptions'),
        ('Targets', 'receivingTargets'),
        ('Receiving Yards', 'receivingYards'),
        ('Touchdowns', 'receivingTouchdowns'),
        ('Yards After Catch', 'receivingYardsAfterCatch'),
        ('Receiving First Downs', '213'),
        ('Receiving 2 Point Conversions', 'receiving2PtConversions'),
        ('Fumbles', 'fumbles'),
        ('Receiving Fumbles', '67'),
        ('Receiving Fumbles Lost', '71'),
        ('Rushing Attempts', 'rushingAttempts'),
        ('Rushing Yards', 'rushingYards'),
        ('Rushing Touchdowns', 'rushingTouchdowns'),
    ]
}

AVERAGE_STATS = {
    'WR': [
        ('Season Average Receptions', 'receivingReceptions'),
        ('Season Average Targets', 'receivingTargets'),
        ('Season Average Receiving Yards', 'receivingYards'),  
        ('Season Average Receiving Yards Per Reception', 'receivingYardsPerReception'), 
        ('Season Average Touchdowns', 'receivingTouchdowns'),
        ('Season Average Yards After Catch', 'receivingYardsAfterCatch'),
        ('Season Average Receiving First Downs', '213'),
        ('Season Average 100-199 Receiving Yard Games', 'receiving100To199YardGame'),
    ],
    'RB': [
        ('Season Average Rushing Attempts', 'rushingAttempts'),
        ('Season Average Rushing Yards Per Attempt', 'rushingYardsPerAttempt'),  
        ('Season Average Receptions', 'receivingReceptions'),
        ('Season Average Targets', 'receivingTargets'),
        ('Season Average Rushing Yards', 'rushingYards'), 
        ('Season Average Receiving Touchdowns', 'receivingTouchdowns'),
        ('Season Average Rushing Touchdowns', 'rushingTouchdowns'),
        ('Season Average Yards After Catch', 'receivingYardsAfterCatch'),
        ('Season Average Fumbles', 'fumbles'),
        ('Season Average First Downs', '213'),
    ],
    'QB': [
        ('Season Average Passing Attempts', 'passingAttempts'),
        ('Season Average Passing Completions', 'passingCompletions'),
        ('Season Average Passing Completion Percentage', 'passingCompletionPercentage'),
        ('Season Average Every 5 Pass Completions', '11'),
        ('Season Average Every 10 Pass Completions', '12'),
        ('Season Average Passing Yards', 'passingYards'),
        ('Season Average Games with 300-399 Passing Yards', 'passing300To399YardGame'),
        ('Season Average Games with 400+ Passing Yards', 'passing400PlusYardGame'),
        ('Season Average Passing Touchdowns', 'passingTouchdowns'),
        ('Season Average Passing 2 Point Conversions', 'passing2PtConversions'),
        ('Season Average Rushing 2 Point Conversions', 'rushing2PtConversions'),
        ('Season Average Passing Interceptions', 'passingInterceptions'),
        ('Season Average Times Sacked Passing', 'passingTimesSacked'),
        ('Season Average Passing Fumbles', '65'),
        ('Season Average Turnovers', 'turnovers'),
        ('Season Average Passing First Downs', '211'),
        ('Season Average Rush Attempts', 'rushingAttempts'),
        ('Season Average Rushing Yards', 'rushingYards'),
        ('Season Average Rushing Touchdowns', 'rushingTouchdowns'),
    ],
    'TE': [
        ('Season Average Receptions', 'receivingReceptions'),
        ('Season Average Targets', 'receivingTargets'),
        ('Season Average Receiving Yards', 'receivingYards'),
        ('Season Average Touchdowns', 'receivingTouchdowns'),
        ('Season Average Yards After Catch', 'receivingYardsAfterCatch'),
        ('Receiving Yards Per Reception', 'receivingYardsPerReception'),
        ('Season Average Receiving First Downs', '213'),
        ('Season Average 100-199 Receiving Yard Games', 'receiving100To199YardGame'),
        ('Season Average Receiving 2 Point Conversions', 'receiving2PtConversions'),
        ('Season Average Fumbles', 'fumbles'),
        ('Season Average Receiving Fumbles', '67'),
        ('Season Average Receiving Fumbles Lost', '71'),
        ('Season Average Rushing Attempts', 'rushingAttempts'),
        ('Season Average Rushing Yards', 'rushingYards'),
        ('Season Average Rushing Touchdowns', 'rushingTouchdowns'),
    ]
}
              