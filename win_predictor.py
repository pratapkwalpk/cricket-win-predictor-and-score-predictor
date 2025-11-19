import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score
import warnings

# Suppress harmless warnings for cleaner output
warnings.filterwarnings('ignore')

print("--- 🏏 Cricket Match Win Predictor (IPL/T20I Only) ---")

# Global variables to store the loaded data, official teams, and configuration
global_data = pd.DataFrame()
global_official_teams = []
global_all_venues = []
global_preprocessor = None
global_model = None
global_team_aliases = {}
global_format_choice = '' 


# ----------------------------------------------------------------------
# --- 1. DATA LOADING AND AGGREGATION FUNCTION (FINAL T20I FIX) ---
# ----------------------------------------------------------------------

def load_and_aggregate_data(format_choice):
    """Loads, cleans, and aggregates data to a consistent match-level format.
    
    The function handles two different data structures:
    1. IPL data (match-level)
    2. T20I data (delivery-level, requiring aggregation)
    """
    
    # 1. File Configuration (Using existing files)
    file_map = {
        'ipl': ['ipl_1.csv'], 
        't20i': ['t20i_data.csv'] 
    }
    
    required_files = file_map.get(format_choice)
    if not required_files:
        print(f"\n❌ Error: Invalid format choice '{format_choice}'.")
        return False

    # Check for file existence and load
    list_of_dfs = []
    for filename in required_files:
        try:
            # Read the CSV, ensuring we drop the unnamed index column which often breaks merges
            df = pd.read_csv(filename)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            list_of_dfs.append(df)
        except FileNotFoundError:
            print(f"\n❌ ERROR: Required file '{filename}' not found for {format_choice.upper()}.")
            return False
        except Exception as e:
            print(f"\n❌ ERROR loading '{filename}': {e}")
            return False
            
    # Concatenate dataframes
    data = pd.concat(list_of_dfs, ignore_index=True)
    print(f"\n✅ Data loaded successfully for {format_choice.upper()}. Total rows: {len(data)}.")

    # 3. Standardize to Match-Level Data for Modeling
    required_final_cols = ['team1', 'team2', 'venue', 'toss_winner', 'toss_decision', 'winner']
    
    if format_choice == 'ipl':
        # IPL Data (ipl_1.csv) is already match-level
        final_data = data[required_final_cols].copy()
        
    elif format_choice == 't20i':
        # T20I FIX: Aggregating delivery data to derive winner
        print("\n⚠️ WARNING: T20I data is delivery-level. Aggregating to match level and inferring winner...")

        # --- STEP 1: Calculate Total Runs Per Team Per Match ---
        # Group by match_id and batting_team to find total score for each team in each match
        scores_summary = data.groupby(['match_id', 'batting_team'])['runs'].sum().reset_index()
        scores_summary.rename(columns={'runs': 'score'}, inplace=True)

        # --- STEP 2: Determine Team 1, Team 2, and Venue for each Match ---
        
        # Identify the two unique teams per match 
        teams_per_match = data.groupby('match_id')['batting_team'].unique().apply(pd.Series)
        teams_per_match.columns = ['team1', 'team2'] 
        teams_per_match = teams_per_match.reset_index()
        
        # Get the venue for the match (first entry is sufficient)
        venue_info = data.groupby('match_id')['venue'].first().reset_index()
        
        # Combine team info and venue info
        final_match_df = teams_per_match.merge(venue_info, on='match_id', how='left')
        
        # Ensure we only proceed with complete match definitions
        final_match_df.dropna(subset=['team1', 'team2', 'venue'], inplace=True)
        
        # --- STEP 3: Merge Scores Using Vectorized Joins (The fix for "inferred 0 matches") ---
        
        # Merge 1: Get Team 1 Score 
        # Joining the match list with the scores list where team1 matches the batting_team
        final_match_df = pd.merge(final_match_df, scores_summary,
                                   left_on=['match_id', 'team1'],
                                   right_on=['match_id', 'batting_team'],
                                   how='left')
        final_match_df.rename(columns={'score': 'team1_score'}, inplace=True)
        final_match_df.drop(columns=['batting_team'], inplace=True, errors='ignore')

        # Merge 2: Get Team 2 Score 
        # Joining the resulting match list with scores list where team2 matches the batting_team
        final_match_df = pd.merge(final_match_df, scores_summary,
                                   left_on=['match_id', 'team2'],
                                   right_on=['match_id', 'batting_team'],
                                   how='left',
                                   suffixes=('_T1', '_T2'))
        final_match_df.rename(columns={'score': 'team2_score'}, inplace=True)
        final_match_df.drop(columns=['batting_team'], inplace=True, errors='ignore')

        # --- STEP 4: Infer Winner ---
        
        # Drop rows where scores are NaN (incomplete data)
        final_match_df.dropna(subset=['team1_score', 'team2_score'], inplace=True)
        
        # Infer Winner based on score comparison
        final_match_df['winner'] = np.where(
            final_match_df['team1_score'] > final_match_df['team2_score'], 
            final_match_df['team1'], 
            final_match_df['team2']
        )
        
        # Filter out tied matches 
        final_match_df = final_match_df[final_match_df['team1_score'] != final_match_df['team2_score']]
        
        # --- STEP 5: Impute Missing Toss Information and Finalize ---
        
        # Toss data is missing, so use required placeholders for the model features
        final_match_df['toss_winner'] = final_match_df['team1'] 
        final_match_df['toss_decision'] = 'Unknown' 
        
        final_data = final_match_df[required_final_cols].copy()
        
        # This count should now be accurate!
        print(f"✅ T20I Winner inferred for **{len(final_data)}** matches.")
        print("⚠️ NOTE: Toss winner and decision are set to placeholders ('Team 1'/'Unknown') as this info is missing in the delivery data.")
        

    # 4. Final Cleaning (Common Steps)
    final_data.dropna(subset=['winner', 'team1', 'team2', 'venue', 'toss_winner', 'toss_decision'], inplace=True)
    
    # Standardize team names for consistency 
    team_mapping = {
        'Rising Pune Supergiants': 'Rising Pune Supergiant',
        'Delhi Daredevils': 'Delhi Capitals',
        'Deccan Chargers': 'Sunrisers Hyderabad',
        'Kings XI Punjab': 'Punjab Kings'
    }
    final_data.replace(team_mapping, inplace=True)
    
    # Update global lists
    global global_data, global_official_teams, global_all_venues
    global_data = final_data
    
    if 'venue' in global_data.columns and 'team1' in global_data.columns and len(global_data) > 0:
        # Get list of all unique teams
        global_official_teams = sorted(global_data['team1'].unique().tolist() + global_data['team2'].unique().tolist())
        global_official_teams = sorted(list(set(global_official_teams)))
        global_all_venues = sorted(global_data['venue'].unique()) 
    else:
        print("\n❌ CRITICAL ERROR: Data aggregation failed. Final DataFrame is empty or missing key columns.")
        return False

    print(f"Total matches loaded: **{len(global_data)}**")
    print(f"Unique Teams: **{len(global_official_teams)}**")
    
    return True

# ----------------------------------------------------------------------
# --- 2. MODEL TRAINING AND UTILITY FUNCTIONS ---
# ----------------------------------------------------------------------

def generate_team_aliases(official_teams):
    """Creates a format-specific alias map and includes user-requested short forms."""
    global global_team_aliases
    aliases = {}
    for team in official_teams:
        aliases[team.lower().strip()] = team
        
        # --- Expanded Team Short Forms ---
        # IPL short forms
        if 'Mumbai Indians' in team: aliases['mi'] = team
        if 'Chennai Super Kings' in team: aliases['csk'] = team
        if 'Sunrisers Hyderabad' in team: aliases['srh'] = team
        if 'Royal Challengers Bangalore' in team: aliases['rcb'] = team
        if 'Kolkata Knight Riders' in team: aliases['kkr'] = team
        if 'Punjab Kings' in team or 'Kings XI Punjab' in team: aliases['pbks'] = team
        if 'Delhi Capitals' in team or 'Delhi Daredevils' in team: aliases['dc'] = team
        if 'Rajasthan Royals' in team: aliases['rr'] = team
        if 'Gujarat Titans' in team: aliases['gt'] = team
        if 'Lucknow Super Giants' in team: aliases['lsg'] = team
            
        # T20I/International short forms
        if 'India' in team: aliases['ind'] = team
        if 'Australia' in team: aliases['aus'] = team
        if 'England' in team: aliases['eng'] = team
        if 'South Africa' in team: aliases['sa'] = team
        if 'New Zealand' in team: aliases['nz'] = team
        if 'Sri Lanka' in team: aliases['sl'] = team
        if 'Pakistan' in team: aliases['pak'] = team
        if 'Bangladesh' in team: aliases['ban'] = team
        if 'West Indies' in team: aliases['wi'] = team
        if 'Afghanistan' in team: aliases['afg'] = team
            
    global_team_aliases = aliases
    print("✅ Aliases established for user-friendly input.")

def train_predictor_model():
    """Trains the Logistic Regression model."""
    global global_preprocessor, global_model
    
    # Check if we have enough data to train
    if len(global_data) < 10:
        print("\n❌ CRITICAL ERROR: Not enough clean match data to train the model. Found less than 10 matches.")
        global_model = None 
        return
    
    global_data['team1_win'] = np.where(global_data['team1'] == global_data['winner'], 1, 0)
    X = global_data[['team1', 'team2', 'venue', 'toss_winner', 'toss_decision']]
    y = global_data['team1_win']

    categorical_features = ['team1', 'team2', 'venue', 'toss_winner', 'toss_decision']

    # Initialize and fit the preprocessor (One-Hot Encoding)
    global_preprocessor = ColumnTransformer(
        transformers=[
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='passthrough'
    )

    X_encoded = global_preprocessor.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42
    )

    global_model = LogisticRegression(solver='liblinear', random_state=42)
    global_model.fit(X_train, y_train)

    y_pred = global_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model trained. Test Accuracy: {accuracy*100:.2f}%")

## ⚙️ Prediction Function
def predict_match_winner(team_a, team_b, venue, toss_winner, toss_decision):
    """Predicts the winner probability for a new match scenario."""
    if global_model is None: 
        print("\n❌ ERROR: Model is not trained. Cannot make prediction.")
        return

    # Check if the requested venue/teams exist in the model's vocabulary
    if venue not in global_all_venues:
         print(f"⚠️ Warning: Venue '{venue}' was not seen in training data. Prediction might be less accurate.")
    if team_a not in global_official_teams or team_b not in global_official_teams:
        print(f"⚠️ Warning: One or both teams ('{team_a}', '{team_b}') were not seen in training data. Prediction might be less accurate.")
    
    new_match_data = pd.DataFrame({
        'team1': [team_a],
        'team2': [team_b],
        'venue': [venue],
        'toss_winner': [toss_winner],
        'toss_decision': [toss_decision]
    })
    
    new_match_encoded = global_preprocessor.transform(new_match_data)
    prediction_proba = global_model.predict_proba(new_match_encoded)[0]
    
    team_a_win_proba = prediction_proba[1]
    team_b_win_proba = prediction_proba[0]
    
    winning_team = team_a if team_a_win_proba > team_b_win_proba else team_b
    
    print("\n--- Match Prediction Result ---")
    print(f"Match: **{team_a}** vs **{team_b}** at {venue}")
    print(f"Toss: {toss_winner} chose to {toss_decision}")
    print(f"**{team_a}** Win Probability: **{team_a_win_proba*100:.2f}%**")
    print(f"**{team_b}** Win Probability: **{team_b_win_proba*100:.2f}%**")
    print(f"\n**Predicted Winner:** **{winning_team}**")

## 👤 User Input Handler
def get_valid_input(prompt, valid_list, context_type):
    """Handles user input validation and alias lookups."""
    # Access the global variables
    global global_format_choice, global_official_teams, global_all_venues 
    
    if context_type == 'team':
        # Use global_format_choice for reliable example display
        if global_format_choice == 'ipl':
            print(f"    (Example IPL aliases: mi, csk, rcb, kkr, srh)")
        elif global_format_choice == 't20i':
            print(f"    (Example T20I aliases: ind, eng, sa, pak, wi)")
        else:
            print(f"    (Available Teams: {', '.join(global_official_teams[:3])}, ...)")
            
    elif context_type == 'venue':
        if global_all_venues: # Only show examples if venues exist
            print(f"    (Available Venues: {', '.join(global_all_venues[:3])}, ...)")

    while True:
        user_input = input(prompt).strip()
        cleaned_input = user_input.lower().strip()
        
        if context_type == 'team':
            if cleaned_input in global_team_aliases:
                return global_team_aliases[cleaned_input]
            else:
                print(f"❌ Invalid team input: '{user_input}'.")
        
        elif context_type == 'venue':
            venue_lower = [v.lower().strip() for v in valid_list]
            if cleaned_input in venue_lower:
                # Return the original, properly capitalized venue name
                return valid_list[venue_lower.index(cleaned_input)]
            else:
                print(f"❌ Invalid venue input: '{user_input}'. Must match an available venue.")
        
        elif context_type == 'decision':
            if cleaned_input in valid_list:
                return cleaned_input
            else:
                print(f"❌ Invalid decision: '{user_input}'. Must be 'bat', 'field', or 'unknown'.")

# ----------------------------------------------------------------------
# --- 5. EXECUTION ---
# ----------------------------------------------------------------------

# 1. Ask user for format
while True:
    format_choice_raw = input("\nSelect Format (IPL / T20I): ").strip().lower()
    if format_choice_raw in ['ipl', 't20i']:
        format_choice = format_choice_raw
        
        # SET GLOBAL FORMAT CHOICE
        global_format_choice = format_choice 
        
        break
    else:
        print("❌ Invalid selection. Please choose 'IPL' or 'T20I'.")

# 2. Load and process data
if not load_and_aggregate_data(format_choice):
    print("\n⚠️ Program stopped due to critical data error. Please check the files.")
    exit()

# 3. Generate Aliases and Train Model
generate_team_aliases(global_official_teams)
train_predictor_model()

# 4. Get Match Details from User
print(f"\n--- 📝 Enter Match Details for **{global_format_choice.upper()}** ---")

# If model training failed, skip prediction input
if global_model is None:
    print("\nCannot proceed with prediction due to insufficient training data.")
    exit()

team_a = get_valid_input("Enter Team 1: ", global_official_teams, 'team')

while True:
    team_b = get_valid_input("Enter Team 2: ", global_official_teams, 'team')
    if team_b != team_a:
        break
    else:
        print("❌ Team 2 must be different from Team 1.")

venue = get_valid_input("Enter Venue: ", global_all_venues, 'venue')
toss_winners = [team_a, team_b]

# T20I-specific logic for toss decision
if global_format_choice == 't20i':
    toss_winner = team_a # Arbitrary selection, as toss data is imputed
    toss_decision = 'Unknown'
    print(f"\n(Toss info automatically set to: {toss_winner} / {toss_decision} due to missing data)")
else:
    toss_winner = get_valid_input(f"Which team won the toss? ({team_a} or {team_b}): ", toss_winners, 'team')
    toss_decisions = ['bat', 'field']
    toss_decision = get_valid_input("Did the toss winner choose to bat or field? (bat/field): ", toss_decisions, 'decision')

# 5. Run the prediction
predict_match_winner(team_a, team_b, venue, toss_winner, toss_decision)