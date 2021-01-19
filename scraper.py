import requests
from bs4 import BeautifulSoup
import csv
import sys
sys.path.append('/test/')

from test import predict

# Get current day NCAA Men's basketball schedule from ESPN
ncaa_schedule_url = 'https://www.espn.com/mens-college-basketball/schedule'
main_page = requests.get(ncaa_schedule_url)

base_url = 'https://www.espn.com'

# Parse the page content
main_soup = BeautifulSoup(main_page.content, 'html.parser')

# Find the html elements representing the teams playing
main_results = main_soup.find(id='sched-container')
team_elems = main_results.find_all(['a', 'span'], class_='team-name')

# Load models
predict.load_models()

# Run prediction on only every two teams
run = False

# Team ID
id = 1

# Loop through each team
# Teams 1 and 2 play each other, 3 and 4 play each other, and so on
for team_elem in team_elems:

    # Create CSV for team matchup
    if run is False:
        with open('./test/game.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['WTeamID', 'WScore', 'LTeamID', 'LScore', 'OppWinPercentage'])
            file.close()

    # Find which teams play today and get the links to their pages
    team_name = team_elem.find('span')
    print(team_name.text)
    if not team_elem.has_attr('href'):
        if run:
            predict.load_data()
            predict.format_data(1, 2)
            predict.predict()
    
        # reset run
        run = not run

        # change id to distinguish between teams
        if id == 1:
            id = 2
        else:
            id = 1
        continue
    team_url = base_url + team_elem['href']

    # From a team's main page, find the link to their schedule
    team_page = requests.get(team_url)
    team_soup = BeautifulSoup(team_page.content, 'html.parser')
    team_results = team_soup.find_all('li', class_='sub')[1]
    sched_url = base_url + team_results.find('a')['href']

    # Use the team's schedule to find each game they play this season
    sched_page = requests.get(sched_url)
    sched_soup = BeautifulSoup(sched_page.content, 'html.parser')
    schedule = sched_soup.find_all('tr')

    # Loop through each game on the team's schedule
    for game in schedule:
        # Find the scores from the games already played
        sched_results = game.find('span', class_='ml4')

        # If a game has no result, it hasn't been played and we skip it
        if sched_results is None:
            continue
        
        # Find the game score, result (W or L), and link to opponent's page
        game_score = sched_results.find('a').text
        game_result = game.find('span', class_=['fw-bold', 'clr-positive']).text

        # Create winning and losing team IDs (current team is always count, opponent is always 0)
        if game_result == 'W':
            w_team_id = id
            l_team_id = 0
        else:
            w_team_id = 0
            l_team_id = id
        opponent = game.find_all('span', class_=['tc', 'pr2'])[1].find('a')
        game_score = game_score.split('-')
        score1 = game_score[0]
        score2 = game_score[1].split(' ')[0]

        if score1 > score2:
            w_score = score1
            l_score = score2
        else:
            w_score = score2
            l_score = score1
        
        # If opponent does not have a url on ESPN, assume their record to be 0
        if opponent is None:
            # set opponent win percentage to 0
            opponent_win_perc = 0
        else:
            # construct opponent url
            opponent_url = base_url + opponent['href']

            # Find opponent record
            opponent_page = requests.get(opponent_url)
            opponent_soup = BeautifulSoup(opponent_page.content, 'html.parser')
            opponent_record = opponent_soup.find('ul', class_='ClubhouseHeader__Record').find('li').text

            # Calculate opponent win percentage
            opponent_record = opponent_record.split('-')
            opp_wins = int(opponent_record[0])
            opp_losses = int(opponent_record[1])
            opponent_win_perc = opp_wins / (opp_wins + opp_losses)

        # Add game data to csv
        with open('./test/game.csv', 'a') as file:
            writer = csv.writer(file)
            writer.writerow([w_team_id, w_score, l_team_id, l_score, opponent_win_perc])
            file.close()

    # Every two teams, run the prediction (wteam is always 1, lteam is always 2)
    if run:
        predict.load_data()
        predict.format_data(1, 2)
        predict.predict()
    
    # reset run
    run = not run

    # change id to distinguish between teams
    if id == 1:
        id = 2
    else:
        id = 1