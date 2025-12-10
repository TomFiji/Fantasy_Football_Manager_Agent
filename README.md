# NFL Fantasy Football Agent System

An AI-powered fantasy football analysis system that provides consistent, data-driven player projections using position-specific agents. Each agent analyzes recent performance, season statistics, teammate injuries, and matchup quality to generate confidence-based recommendations.

## 🎯 Overview

This project deploys specialized AI agents for each fantasy-relevant position (QB, RB, WR, TE) that follow rigorous analytical frameworks to produce reliable player projections. The system prioritizes recent form equally with season-long performance while factoring in critical context like injuries and defensive matchups.

## ✨ Key Features

- **Position-Specific Agents**: Dedicated agents for QB, RB, WR, and TE with tailored analysis frameworks
- **Consistent Scoring System**: Standardized 0-10 scoring scale across all positions
- **Multi-Factor Analysis**: 
  - Recent Performance (Last 3 Weeks): 40%
  - Season Statistics: 40%
  - Teammate Injuries: 15%
  - Matchup Quality: 5%
- **Real-Time Data Integration**: Pulls live stats, injury reports, and defensive rankings
- **Actionable Insights**: Concise takeaways for fantasy decision-making

### Installation

1. Clone the repository
```bash
git clone https://github.com/tomfiji/Fantasy_Football_Manager_Agent
```

2. Create virtual environment and install all dependencies
```bash
cd C:/Users/username/projects/Fantasy_Football_Manager_Agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables

Create a `.env` file in the backend directory:
```
SUPABASE_URL= your_supabase_project_url
SUPABASE_ANON_KEY= your_supabase_project_anon_key
SUPABASE_SERVICE_ROLE_KEY= your_supabase_project_role_key
GOOGLE_API_KEY= your_gemini_api_key
ESPN_LEAGUE_ID= your_espn_league_id
ESPN_SWID_COOKIE= your_espn_swid_cookie
ESPN_S2_COOKIE= your_espn_s2_cookie
MY_TEAM_ID= your_team_id
ESPN_CLIENT_PATH= your_directory_to_the_espn_client
```

4. Set up the database

Create the following tables in your Supabase project:

**player_weekly_stats:**
```sql
create table public.player_weekly_stats (
  player_id integer not null,
  player_name text not null,
  week integer not null,
  stats_breakdown jsonb not null,
  points real null default 0,
  cached_at timestamp without time zone null default CURRENT_TIMESTAMP,
  constraint player_weekly_stats_pkey primary key (player_id, week)
) TABLESPACE pg_default;

create index IF not exists idx_player_week on public.player_weekly_stats using btree (player_id, week) TABLESPACE pg_default;

create index IF not exists idx_stats_breakdown on public.player_weekly_stats using gin (stats_breakdown) TABLESPACE pg_default;
```

5. Run the application
```bash
*/venv/Scripts/python.exe
```

Visit `http://localhost:5173` to see the app.

## 🏗️ System Architecture

### Agent Weighting Framework

All position agents use the same weighting system to ensure consistency:

```
┌─────────────────────────────────────────────────────────┐
│  WEIGHTING DISTRIBUTION                                 │
├─────────────────────────────────────────────────────────┤
│  Recent Form (Last 3 Weeks)      40%  ████████████████  │
│  Season Baseline Statistics      40%  ████████████████  │
│  Teammate Injury Impact          15%  ███████           │
│  Defensive Matchup Quality        5%  ██                │
└─────────────────────────────────────────────────────────┘
```

### Position-Specific Tiers

#### Wide Receiver
- **Elite (9-10)**: 8+ targets/game, 90+ yards/game, 0.6+ TD/game
- **WR1 (7-8)**: 7+ targets/game, 70+ yards/game, 0.5+ TD/game
- **WR2 (5-6)**: 6+ targets/game, 55+ yards/game, 0.4+ TD/game
- **WR3 (3-4)**: 5+ targets/game, 45+ yards/game, 0.3+ TD/game
- **Flex (1-2)**: Below WR3 thresholds

#### Running Back
- **Elite (9-10)**: 18+ touches/game, 100+ total yards/game, 0.8+ TD/game
- **RB1 (7-8)**: 15+ touches/game, 80+ total yards/game, 0.6+ TD/game
- **RB2 (5-6)**: 12+ touches/game, 60+ total yards/game, 0.5+ TD/game
- **RB3 (3-4)**: 10+ touches/game, 45+ total yards/game, 0.3+ TD/game
- **Flex (1-2)**: Below RB3 thresholds

#### Quarterback
- **Elite (9-10)**: 35+ attempts/game, 280+ pass yards/game, 2.0+ pass TD/game
- **QB1 (7-8)**: 30+ attempts/game, 240+ pass yards/game, 1.5+ pass TD/game
- **QB2 (5-6)**: 28+ attempts/game, 220+ pass yards/game, 1.2+ pass TD/game
- **Streaming (3-4)**: 25+ attempts/game, 200+ pass yards/game, 1.0+ pass TD/game
- **Bench (1-2)**: Below streaming thresholds

#### Tight End
- **Elite (9-10)**: 7+ targets/game, 70+ yards/game, 0.6+ TD/game
- **TE1 (7-8)**: 6+ targets/game, 55+ yards/game, 0.5+ TD/game
- **TE2 (5-6)**: 5+ targets/game, 45+ yards/game, 0.4+ TD/game
- **Streaming (3-4)**: 4+ targets/game, 35+ yards/game, 0.3+ TD/game
- **Bench (1-2)**: Below streaming thresholds

## 📊 Data Sources

### Statistics Tracked

#### Wide Receiver Stats
**Weekly/Season Totals:**
- Receptions, Targets, Receiving Yards
- Touchdowns (by yardage range: 0-9, 10-19, 20-29, 30-39, 50+)
- Yards After Catch, First Downs
- Catch Rate Percentage, Fantasy Points per Target
- Milestone Bonuses (Every 5/10 receptions)

**Season Averages:**
- Per-game metrics for all above stats
- 100-199 yard game frequency
- Yards per reception efficiency

#### Running Back Stats
**Weekly/Season Totals:**
- Rushing Attempts, Rushing Yards, Rushing Touchdowns
- Receptions, Targets, Receiving Yards, Receiving Touchdowns
- Yards After Catch, First Downs, Fumbles
- 100-199 yard games, 200+ yard games
- 50+ yard rushing TDs

**Season Averages:**
- Per-game metrics for rushing and receiving
- Yards per attempt efficiency
- Milestone reception bonuses

#### Quarterback Stats
**Weekly/Season Totals:**
- Passing: Attempts, Completions, Yards, Touchdowns, Interceptions
- Rushing: Attempts, Yards, Touchdowns, Yards per Attempt
- Completion Percentage, Times Sacked
- Turnovers, Fumbles, First Downs
- 2-Point Conversions (passing and rushing)

**Season Averages:**
- Per-game metrics for all passing/rushing stats
- 300-399 and 400+ yard game frequency
- Completion milestone bonuses

#### Tight End Stats
**Weekly/Season Totals:**
- Receptions, Targets, Receiving Yards, Touchdowns
- Yards After Catch, First Downs
- Fumbles (total, receiving, lost)
- 100-199 yard games
- 2-Point Conversions

**Season Averages:**
- Per-game metrics for all receiving stats
- Yards per reception efficiency
- Catch rate percentage

## 🔧 Tools & Functions

Each agent has access to the following tools:

### Core Statistics Functions
- `get_current_week()` - Returns current NFL week
- `get_aggregate_stats()` - Returns season total statistics
- `get_average_stats()` - Returns per-game season averages
- `get_player_recent_performance()` - Returns last 3 weeks of stats

### Intelligence Tool
- `search_tool` - Real-time web search for:
  - Team injury reports
  - Breaking news and status updates

## 📈 Analysis Workflow

Each agent follows a standardized 5-step process:

### Step 1: Data Gathering
- Retrieve current NFL week
- Pull last 3 weeks of player stats
- Fetch season aggregate and average stats
- Search injury reports and defensive rankings

### Step 2: Recent Form Analysis (40% Weight)
- Calculate 3-week averages for key metrics
- Compare to season averages
- Assign trend score (-3 to +3 scale)
- Weight: 40% of final score

### Step 3: Season Baseline (40% Weight)
- Evaluate season-long performance
- Calculate per-game averages
- Assign tier (Elite/Starter/Flex/Bench)
- Weight: 40% of final score

### Step 4: Injury Impact (15% Weight)
- Assess teammate injury situations
- Calculate target/touch opportunity changes
- Note: QB logic is inverse (healthy weapons = positive)
- Weight: 15% of final score

### Step 5: Matchup Quality (5% Weight)
- Evaluate defensive ranking (1-32 scale)
- Assign matchup difficulty score
- Weight: 5% of final score

### Final Output
- Weighted total score (0-10 scale)


```

## 🚀 Usage Example

```python
# Example: Analyzing a Wide Receiver
wr_runner = InMemoryRunner(agent=wr_agent, app_name='agents')
response = await wr_runner.run_debug("What wide receivers should I start this week?")

# Example Output of 1 WR:
#**Player: Michael Wilson (ARI)**

# **STEP 1 - GATHER DATA**
# *   `player_id`: 4360761
# *   `position`: 'WR'
# *   `team`: 'ARI'
# *   `opponent`: 'LAR'
# *   `opponent_rank_against_WRs`: 19
# *   `injury_status`: 'ACTIVE'
# wr_agent > **Michael Wilson Analysis:**

# **STEP 2 - RECENT FORM ANALYSIS (40% weight)**
# *   Week -3 (Week 11): Targets: 18, Receptions: 15, Receiving Yards: 185, Touchdowns: 0, Catch Rate: 0.83
# *   Week -2 (Week 12): Targets: 15, Receptions: 10, Receiving Yards: 118, Touchdowns: 0, Catch Rate: 0.67
# *   Week -1 (Week 13): Targets: 7, Receptions: 3, Receiving Yards: 36, Touchdowns: 0, Catch Rate: 0.43

# *3-week Averages:*
# *   Targets: 13.33
# *   Receptions: 9.33
# *   Receiving Yards: 113.0
# *   Touchdowns: 0.0
# *   Catch Rate: 0.643

# *Season Averages:*
# *   Targets: 6.5
# *   Receptions: 4.17
# *   Receiving Yards: 47.5
# *   Touchdowns: 0.08
# *   Catch Rate: 0.64

# *Comparison:*
# *   Targets: Trending significantly UP (105%)
# *   Receptions: Trending significantly UP (123.7%)
# *   Receiving Yards: Trending significantly UP (137.9%)
# *   Touchdowns: Trending significantly DOWN (-100%)
# *   Catch Rate: Consistent (0.47%)

# Recent Form Score: 8.5/10 points

# **STEP 3 - SEASON BASELINE (40% weight)**
# *   Season total targets: 78
# *   Season total receptions: 50
# *   Season total yards: 570
# *   Season total touchdowns: 1
# *   Per game averages: 6.5 targets, 4.17 receptions, 47.5 yards, 0.08 touchdowns
# *   Efficiency: 11.4 yards per reception, 64% catch rate
# *   Milestone bonuses: 2 games with 100-199 receiving yards

# Assign tier based on per-game averages:
# *   Targets: 6.5 (WR2)
# *   Yards: 47.5 (WR3)
# *   Touchdowns: 0.08 (Below WR3 threshold)

# Season Baseline Score: 5/10 points (Solid WR2/WR3 in volume and yards, but very low touchdowns)

# **STEP 4 - TEAMMATE INJURIES (15% weight)**
# Marvin Harrison Jr. (WR1) was DNP Wednesday due to a heel injury. Greg Dortch (WR) was also DNP with a chest injury. If Harrison Jr. is out or limited, Wilson's target share could significantly increase.

# Injury Impact Score: +4/5 points

# **STEP 5 - MATCHUP QUALITY (5% weight)**
# *   Opponent: Los Angeles Rams
# *   Opponent Rank Against WRs: 19 (Average matchup)

# Matchup Score: 0/2 points

# **FINAL CALCULATION (Michael Wilson):**
# *   Recent Form: 8.5 * 0.40 = 3.4
# *   Season Baseline: 5 * 0.40 = 2.0
# *   Injury Impact: 4 * 0.15 = 0.6
# *   Matchup: 0 * 0.05 = 0.0
# *   **TOTAL SCORE: 6.0/10**

# ---
```

## 🔍 Position-Specific Considerations

### Wide Receivers
- **Volume is king**: Target share drives opportunity
- **Injury beneficiary**: WR2/TE1 absences boost targets
- **Catch rate trends**: Efficiency indicator for recent form

### Running Backs
- **Touches = opportunity**: Rush attempts + receptions
- **Backfield context**: Injury impact is massive for RBs
- **Dual-threat value**: Receiving work stabilizes floor

### Quarterbacks
- **Inverse injury logic**: Healthy weapons = better performance
- **Turnover awareness**: INTs and fumbles kill fantasy scores
- **Rushing upside**: Mobile QBs have significantly higher ceilings
- **O-line matters**: Sacks indicate pressure/poor protection

### Tight Ends
- **TD-dependent**: Lower volume, need red zone usage
- **WR injury boost**: Benefits when WRs are out
- **Blocking role risk**: Injuries may limit route participation
- **Elite tier is rare**: Only handful reach top-tier volume

## 📋 Injury Impact Scoring

### Wide Receiver & Tight End
- **+4**: WR1 teammate out → Player becomes clear alpha
- **+3**: WR2 teammate out → Significant target increase
- **+2**: TE1 out (for WR) / WR2 out (for TE) → Moderate increase
- **+1**: Minor teammate injury
- **0**: Full weapons healthy
- **-1**: This player returning from injury

### Running Back
- **+4**: Starting RB out → Backup becomes bellcow
- **+3**: Co-RB out → Clear lead back role
- **+2**: Goal-line RB out → Red zone opportunities
- **+1**: Minor backfield injury
- **0**: No injuries
- **-1**: This player returning from injury

### Quarterback (Inverse Logic)
- **+4**: WR1 + WR2 healthy, elite weapons available
- **+3**: Primary receiving weapons healthy
- **+2**: Key WR/TE returning from injury
- **+1**: TE1 or RB1 healthy (checkdown options)
- **0**: Average weapons situation
- **-1**: WR1 or WR2 out
- **-2**: Multiple key pass catchers out
- **-3**: O-line injuries (pressure/sack concerns)

## 🎲 Matchup Scoring (All Positions)

Defense rankings use 1-32 scale where **1 = easiest matchup**

- **-2 points**: Rank 1-5 (Nightmare matchup)
- **-1 point**: Rank 6-12 (Tough matchup)
- **0 points**: Rank 13-20 (Average matchup)
- **+1 point**: Rank 21-28 (Good matchup)
- **+2 points**: Rank 29-32 (Elite matchup)

## 🛠️ Technical Implementation

### Agent Structure
Each position agent is built with:
- Standardized prompt engineering for consistency
- Tool-calling architecture for data retrieval
- Structured output formatting
- Weighted scoring calculations

### Data Flow
```
User Request
    ↓
Agent Selection (QB/RB/WR/TE)
    ↓
Tool Calls (get_current_week, get_stats, search_tool)
    ↓
Data Processing & Calculation
    ↓
Weighted Score Aggregation
    ↓
Formatted Output
```

## 🧮 Scoring Formula

```python
final_score = (
    recent_form_score * 0.40 +
    season_baseline_score * 0.40 +
    injury_impact_score * 0.15 +
    matchup_score * 0.05
)

[final_score]
```

## 📝 Output Format

Every positional agent produces consistent output:

```
PLAYER: [Player Name]
OPPONENT: [Team] (Defense Rank vs [Position]: X/32)

RECENT FORM (Last 3 Weeks): X/10
[Trend analysis summary]

SEASON BASELINE: X/10
[Tier and key statistics]

INJURY IMPACT: X/5
[Context and opportunity changes]

MATCHUP QUALITY: X/2
[Matchup assessment]

TOTAL SCORE: X.X/10

```
Lineup Agent produces an all-in-one starting lineup output:
```
============================================================
STARTING LINEUP
============================================================
WR: Nico Collins: Collins receives a 3.9/10 score, showing positive trends in recent receptions and yards, though targets and touchdowns are down. He maintains WR1-tier season averages, but his overall outlook is negatively impacted by a 'nightmare' matchup against a tough defense., Alec Pierce: Pierce's score is 3.25/10. His recent form is mixed, with declining targets but a significant boost in touchdowns, showcasing big-play ability. He's categorized as a WR3 based on season averages and benefits from a 'good' matchup this week.
RB: Josh Jacobs: Jacobs is recommended as a starter due to his strong season baseline, averaging 19.55 touches, 91.36 total yards, and 1 touchdown per game. Despite a recent downtrend in receiving and touchdowns and a questionable knee status, he faces an average matchup against Chicago., Michael Carter: Carter gets the nod as a starter due to significant injuries to fellow running backs James Conner (IR) and Trey Benson (unlikely to return), which should lead to a substantial increase in his workload. His recent receiving volume is trending significantly upward, despite facing a challenging matchup against the Rams.
TE: Juwan Johnson: Johnson is the top TE recommendation due to strong upward trends in recent targets, receptions, and receiving yards, along with a recent touchdown. His potential is further boosted by WR Chris Olave's limited availability, which should increase his target share.
QB: Sam Darnold: Darnold's recent performance is below his season averages, especially in touchdowns and turnovers, which is a major concern. Although his season baseline ranks him as a high-end QB2, his recent slump, offensive line injuries, and a tough matchup against Atlanta temper expectations. He is the only QB option, so start with caution.

============================================================
FLEX CANDIDATES
============================================================
FLEX: Zach Ertz: Ertz ties with Johnson in score, showing strong recent volume with 8.67 targets, 6 receptions, and 67.33 receiving yards per game. However, a recent lack of touchdowns, including a 13-target game without a score, is a concern. He faces a good matchup against Minnesota., Darren Waller: Waller, with a 3.4/10 score, recently returned from IR and demonstrated good receiving yards in his first game back. With Tyreek Hill out for the season, Waller is expected to become a primary receiving option, providing a significant boost to his potential workload., Omarion Hampton: Hampton scores 2.3/10, as he is returning from an ankle injury and had limited practice participation, raising concerns about his snap count and readiness. While his season averages suggested RB1 potential in touches and yards, his recent lack of game action and lower touchdown rate make him a riskier play.
============================================================
```

## 🎓 Best Practices

### For Accurate Analysis
1. **Always check injury reports** - Search team injury news before each analysis
2. **Consider recent trends** - Last 3 weeks carry equal weight to full season
3. **Factor in context** - Injuries and matchups provide critical nuance
4. **Trust the system** - Consistent methodology prevents bias


## 🔮 Future Enhancements

Potential additions to the system:
- Weather impact analysis
- Home/away splits
- Divisional matchup history
- Vegas betting line integration
- Snap count trending
- Route participation metrics
- Red zone usage tracking
- Advanced efficiency metrics (EPA, DVOA)

## 📊 Success Metrics

The system aims to provide:
- **Consistency**: Same framework applied across all analyses
- **Transparency**: Clear scoring breakdown and reasoning
- **Actionability**: Confidence ratings drive start/sit decisions
- **Accuracy**: Data-driven projections with contextual awareness

## 🎓 What I Learned

- **AI Agent Prompting**: My initial prompt wouldn't output a consistent result so after multiple trial and errors I finished with the formula currently implemented
- **Multi Agent Architecture**: Implemented multiple agents knowing that there was going to be one lineup agent that processed all their data into a starting lineup and flex position candidates
- **Google's Agent Development Kit**: I had to read documentation and dig into different methods to debug and solve problems with AI output and agent errors



## 👤 Author

**Tom Fijalkowski**
- GitHub: [@TomFiji](https://github.com/tomfiji)
- LinkedIn: [Tom Fijalkowski](https://linkedin.com/in/tom-fijalkowski)
- Email: tf.tomfijalkowski@gmail.com

---

**Built with AI-powered analysis to take the guesswork out of fantasy football decisions.**