import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from supabase_client import supabase
from googlesearch import search
from utils.espn_client import my_team, league

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
            my_players.append({"player_name": player.name, "player_id": player.playerId, "team": player.proTeam, "opponent": player.pro_opponent, f"opponent_rank_against_{position}s": player.pro_pos_rank, "injury_status": player.injuryStatus})
    return my_players


def search_web(query: str) -> str:
    try:
        results = search(query, num_results=3)
        formatted_results = []
        for r in results:
            formatted_results.append(
                f"Title: {r.title}\nSnippet: {r.description}\nSource: {r.url}"
            )
        
        if not formatted_results:
            return "No search results found."
        
        return "\n\n".join(formatted_results)
    
    except TypeError:
        return(
            "Error: 'advanced=True' is not supported. Please ensure you installed "
            "'googlesearch-python' and not just 'googlesearch'."
        )
    except Exception as e:
        return f"Error performing search: {e}"

def get_external_analysis(player_name: str, team_name: str) -> dict:
    """
    Performs specific web searches for injury, o-line, and teammate room health 
    and returns a compiled report.
    """
    
    # 1. Query the search tool for injury only
    injury_query = f"{player_name} week {get_current_week()} injury status fantasy"
    injury_result = search_web(query=injury_query) 
    
    # 2. Query the search tool for O-Line
    oline_query = f"{team_name} offensive line health report"
    oline_result = search_web(query=oline_query)
    
    #3. Query the search tool for teammate health
    teammate_query = f"{player_name} teammate health week {get_current_week()} injury status fantasy"
    teammate_result = search_web(query=teammate_query)
    
    return {"injury_report": injury_result, "oline_report": oline_result, "teammate_report": teammate_result}

    
   
def post_week_stats(player, position: str):
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
              