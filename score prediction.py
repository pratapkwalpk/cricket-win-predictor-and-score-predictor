import random
# Defining teams allowed for each format 
ALLOWED_TEAMS = {
    'IPL': [
        "CSK", "MI", "RCB", "KKR", "SRH", "DC", "PBKS", "RR", "LSG", "GT",
    
    ],
    'T20': [
        "IND", "ENG", "AUS", "PAK", "NZ", "SA", "WI", "SL", "BAN", "AFG", "ZIM", "NED", "IRE", "NAM", "SCO",
        
    ],
    'ODI': [
        "IND", "ENG", "AUS", "PAK", "NZ" , "SA", "BAN", "AFG", "SL", "WI",
        
    ]
}

def check_valid_team(team_name, format_key):
    """Checks if the team name is valid for the selected format."""
    allowed_list = [team.upper() for team in ALLOWED_TEAMS.get(format_key, [])]
    return team_name.upper() in allowed_list

# --- Step 1: Format Selection and Validation ---
print("Welcome to Cricket Score Predictor!")
print("ONLY TEST PLAYING NATIONS ALLOWED FOR T20 AND ODI FORMATS.")

print("Which format is it:")
match_format = input("Enter 'T20', 'IPL', or 'ODI': ").upper()

if match_format not in ['T20', 'IPL', 'ODI']:
    print("Invalid match format entered. Exiting.")
    quit()
else:
    print(f"Format set to {match_format}. Allowed teams: {ALLOWED_TEAMS[match_format]}")

#check if  teams are valid and adding them
while True:
    team1 = input(f"Enter the First team (from {match_format} list): ")
    if check_valid_team(team1, match_format):
        break
    print(f"'{team1}' is not a valid team for {match_format}. Please try again.")

while True:
    team2 = input(f"Enter the second team (from {match_format} list): ")
    if check_valid_team(team2, match_format) and team2.upper() != team1.upper():
        break
    elif team2.upper() == team1.upper():
        print(f"'{team2}' is already entered as Team 1. Please enter a different team.")
    else:
        print(f"'{team2}' is not a valid team for {match_format}. Please try again.")

# entering Batting Team and Match Status 
while True:
    team_playing = input("Who is doing batting: ")
    if team_playing.upper() == team1.upper() or team_playing.upper() == team2.upper():
        break
    else:
        print(f"You entered '{team_playing}' which is not one of the playing teams: {team1} or {team2}")

is_match_started = input("Is Match Started[Y/N]: ")
is_match_started = is_match_started.upper()

while True:
    if is_match_started.upper() == 'Y' or is_match_started.upper() == 'N':
        break
    print("Wrong Input Please Try Again")
    is_match_started = input("Is Match Started[Y/N]: ")
    is_match_started = is_match_started.upper()

#Core Prediction Logic
if is_match_started == 'Y':
    # Getting current score details
    overs = int(
        input("Please tell how many overs completed (only over not balls): "))
    runs = int(input("Please tell how many run are: "))
    wickets = int(input("Please tell how many wickets are taken: "))
    
    if wickets < 0:
        print("Sorry, this is not possible (negative wickets).")
        quit()
    if overs <= 0:
        print("Please tell after minimum 1 over.")
        quit()
    
    # Calculate Run Rate
    rr = runs / overs
    print(f"Hmm.... Current Run Rate is {rr:.2f}")

    # ///////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    #               T20 / IPL BLOCK
    # ///////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    if match_format == 'T20' or match_format == 'IPL':
        TOTAL_OVERS = 20
        # Format-specific random adjustments
        RPO_ADJ_LIST = [1.0, 0.5, 0.1, 0.8, 0.45, 0.68]
        RR_BOOST_LIST = [1.0, 2.0, 0.5, 0.8, -0.1, -0.3]
        overs_mark = 9 
        rr_check = 9.0
        
        # Initial checks
        if overs >= TOTAL_OVERS:
            print(f"I think you are late, the innings is {TOTAL_OVERS} overs.")
            quit()
        if wickets >= 10:
            print(f"10 wickets are over! {team_playing} made {runs} runs.")
            quit()

        # Run Rate Adjustment (using the fixed compound assignment)
        neg_or_pos = random.randint(0, 1)
        rpo_changer = RPO_ADJ_LIST[random.randint(0, len(RPO_ADJ_LIST) - 1)]

        if neg_or_pos == 0:
            rr -= rpo_changer
        elif neg_or_pos == 1:
            rr += rpo_changer
        
        # Wickets 0-3 (High Score Potential)
        if wickets <= 3:
            if (overs < overs_mark and rr > rr_check) or (overs >= overs_mark):
                predict = int(rr * TOTAL_OVERS)
                print(f"Prediction: They will score between {predict - 4} and {predict + 3} runs.")
            else:
                print(f"{team_playing} are slow but may accelerate: ")
                rr += RR_BOOST_LIST[random.randint(0, len(RR_BOOST_LIST) - 1)]
                predict = int(rr * TOTAL_OVERS)
                print(f"Prediction: They can score between {predict - 3} and {predict + 4} runs.")

        # Wickets 4-7 (Mid-range Score Potential)
        elif wickets > 3 and wickets <= 7:
            to_minus = random.randint(9, 24)
            if (overs < overs_mark and rr > rr_check) or (overs >= overs_mark):
                predict = int(rr * TOTAL_OVERS) - to_minus
                print(f"Prediction: They will score between {predict - 2} and {predict + 3} runs.")
            else:
                print(f"{team_playing} are slow but may accelerate: ")
                rr += RR_BOOST_LIST[random.randint(0, len(RR_BOOST_LIST) - 1)]
                predict = int(rr * TOTAL_OVERS) - to_minus
                print(f"Prediction: They can score between {predict - 3} and {predict + 2} runs.")

        # Wickets 7+ (Low Score Potential)
        elif wickets >= 7:
            to_minus = random.randint(18, 40)
            if (overs < overs_mark and rr > rr_check) or (overs >= overs_mark):
                predict = int(rr * TOTAL_OVERS) - to_minus
                print(f"Prediction: They will score between {predict - 1} and {predict + 3} runs.")
            else:
                print(f"{team_playing} are very slow, low chance of a comeback: ")
                rr += RR_BOOST_LIST[random.randint(0, len(RR_BOOST_LIST) - 1)]
                predict = int(rr * (TOTAL_OVERS * 0.75)) - to_minus # Weighted for final overs
                print(f"Prediction: They can score between {predict - 2} and {predict + 1} runs.")

    # /////////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\
    #                ODI BLOCK
    # ///////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\
    elif match_format == 'ODI':
        TOTAL_OVERS = 50
        # Format-specific random adjustments (smaller change)
        RPO_ADJ_LIST = [0.4, 0.2, 0.05, 0.3, 0.15, 0.25]
        RR_BOOST_LIST = [0.5, 1.0, 0.3, 0.4, -0.05, -0.15]
        overs_mark = 22 # Approx 45% of 50
        rr_check = 6.0 # Lower run rate check
        
        if overs >= TOTAL_OVERS:
            print(f"I think you are late, the innings is {TOTAL_OVERS} overs.")
            quit()
        if wickets >= 10:
            print(f"10 wickets are over! {team_playing} made {runs} runs.")
            quit()

        # Run Rate Adjustment
        neg_or_pos = random.randint(0, 1)
        rpo_changer = RPO_ADJ_LIST[random.randint(0, len(RPO_ADJ_LIST) - 1)]

        if neg_or_pos == 0:
            rr -= rpo_changer
        elif neg_or_pos == 1:
            rr += rpo_changer
        
        # Wickets 0-3 (High Score Potential)
        if wickets <= 3:
            if (overs < overs_mark and rr > rr_check) or (overs >= overs_mark):
                predict = int(rr * TOTAL_OVERS)
                print(f"Prediction: They will score between {predict - 5} and {predict + 5} runs.")
            else:
                print(f"{team_playing} are consolidating but likely to accelerate: ")
                rr += RR_BOOST_LIST[random.randint(0, len(RR_BOOST_LIST) - 1)]
                predict = int(rr * TOTAL_OVERS)
                print(f"Prediction: They can score between {predict - 4} and {predict + 6} runs.")

        # Wickets 4-7 (Mid-range Score Potential)
        elif wickets > 3 and wickets <= 7:
            to_minus = random.randint(25, 60) # Larger ODI deduction
            if (overs < overs_mark and rr > rr_check) or (overs >= overs_mark):
                predict = int(rr * TOTAL_OVERS) - to_minus
                print(f"Prediction: They will score between {predict - 8} and {predict + 5} runs.")
            else:
                print(f"{team_playing} are consolidating but may accelerate: ")
                rr += RR_BOOST_LIST[random.randint(0, len(RR_BOOST_LIST) - 1)]
                predict = int(rr * TOTAL_OVERS) - to_minus
                print(f"Prediction: They can score between {predict - 6} and {predict + 5} runs.")

        # Wickets 7+ (Low Score Potential)
        elif wickets >= 7:
            to_minus = random.randint(45, 100) # Much larger ODI deduction
            if (overs < overs_mark and rr > rr_check) or (overs >= overs_mark):
                predict = int(rr * TOTAL_OVERS) - to_minus
                print(f"Prediction: They will score between {predict - 4} and {predict + 6} runs.")
            else:
                print(f"{team_playing} are struggling with low chances of a good finish: ")
                rr += RR_BOOST_LIST[random.randint(0, len(RR_BOOST_LIST) - 1)]
                predict = int(rr * (TOTAL_OVERS * 0.75)) - to_minus # Weighted for final overs
                print(f"Prediction: They can score between {predict - 10} and {predict + 5} runs.")
# End of Core Prediction Logic 

elif is_match_started == 'N':
    print("Please come after MATCH IS STARTED")