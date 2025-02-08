import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import flask_login
from nba_api.stats.endpoints import playercareerstats, commonteamroster
from nba_api.stats.static import players, teams
import pandas
import joblib
import requests
import datetime
from bs4 import BeautifulSoup
import dcl
from PIL import Image
from io import BytesIO
import subprocess

# Sets up the flask app
app = Flask(__name__)
app.config['RECAPTCHA_S8ITE_KEY'] = '6LcYcEohAAAAANVL5nwJ25oOM488BPaC9bujC-94'
app.secret_key = '6LcYcEohAAAAAJ5JeDLnVKReHLj0ZIkeo7FgilZB'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
db = SQLAlchemy(app)

# Sets up the login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class User(flask_login.UserMixin):
    pass


# Sets up the database
class LoginScreen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usernames = db.Column(db.String(100), nullable=False)
    passwords = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return 'User ' + str(self.id)


db.create_all()
db.session.commit()

# Sets up machine learning models
kmg = joblib.load('kmeans_model_guard.sav')
scalerg = joblib.load('scaler_guard.gz')

kmw = joblib.load('kmeans_model_wing.sav')
scalerw = joblib.load('scaler_wing.gz')

kmb = joblib.load('kmeans_model_big.sav')
scalerb = joblib.load('scaler_big.gz')

xgb = joblib.load('statPrediction.sav')

# Finds todays date
yr = datetime.date.today().year
month = datetime.date.today().month

# Scrapes basketball reference, uses today's date to determine what season we are in right now
if month >= 11:
    basic = f"https://www.basketball-reference.com/leagues/NBA_{yr + 1}_per_game.html"
    advanced = f"https://www.basketball-reference.com/leagues/NBA_{yr + 1}_advanced.html"
    season = yr + 1
else:
    basic = f"https://www.basketball-reference.com/leagues/NBA_{yr}_per_game.html"
    advanced = f"https://www.basketball-reference.com/leagues/NBA_{yr}_advanced.html"
    season = yr

# Requests the page based on the above urls
basic_page = requests.get(basic)
advanced_page = requests.get(advanced)

# Sets up beautiful soup object
basic_soup = BeautifulSoup(basic_page.content, "html.parser")
advanced_soup = BeautifulSoup(advanced_page.content, "html.parser")

# Finds the table based on the id
basic_table = basic_soup.find(id='per_game_stats')
advanced_table = advanced_soup.find(id='advanced')

# Converts the table to a dataframe
basic_df = pandas.read_html(str(basic_table))[0]
advanced_df = pandas.read_html(str(advanced_table))[0]

# Converted accented characters to non-accented characters because the nba api in the flask doesn't have accents
cleaned_players = []
for player in basic_df['Player']:
    cleaned_players.append(dcl.clean_diacritics(player))

basic_df = basic_df.assign(Player=cleaned_players)

cleaned_players = []
for player in advanced_df['Player']:
    cleaned_players.append(dcl.clean_diacritics(player))

advanced_df = advanced_df.assign(Player=cleaned_players)

# Replaced all stats with a blank spot with 0 so I wouldn't have to remove some key nba players
basic_df.fillna(0, inplace=True)
advanced_df.fillna(0, inplace=True)


# 401 page if user tries to access material without logging in
@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401


# Loads a user in a session
@login_manager.user_loader
def user_loader(username):
    if username not in username:
        return

    user = User()
    user.id = username
    return user


# Redirects user to login page when they log out
@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))


# App route for login page
@app.route('/', methods=['GET', 'POST'])
def login():
    # Runs when user presses log in on the login page
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Checks if username is in database
        if bool(LoginScreen.query.filter_by(usernames=username).first()):
            id_checker = LoginScreen.query.filter_by(usernames=username).first()
            id_checker = id_checker.id
            id_tester = LoginScreen.query.get(id_checker).passwords
            # Checks if username and password match
            if password == id_tester:
                user = User()
                user.id = username
                flask_login.login_user(user)
                return redirect(url_for('protected'))

            else:
                return render_template('wrongCredentials.html')
        else:
            return render_template('wrongCredentials.html')
    else:
        return render_template('login.html')


# App route for sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Runs when user presses sign up
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirmpassword']
        # Ensures both password fields match
        if password == confirm:
            signin = LoginScreen(usernames=username, passwords=password)
            # Checks if username already exists
            if bool(LoginScreen.query.filter_by(usernames=username).first()):
                return render_template('existingUser.html')
            else:
                db.session.add(signin)
                db.session.commit()
                id_checker = LoginScreen.query.filter_by(usernames=username).first()
                id_checker = id_checker.id
                user = User()
                user.id = username
                flask_login.login_user(user)
                return redirect(url_for('protected'))
        else:
            return render_template('confirmPassword.html')
    else:
        return render_template('signup.html')


# App route for home page - Only accessible once you log in or create an account
@app.route('/protected', methods=['GET', 'POST'])
@flask_login.login_required
def protected():
    # Runs when user clicks one of the two buttons
    if request.method == 'POST':
        # Logs user out if log out button is clicked
        if request.form['Submit'] == "Log Out":
            return redirect(url_for('logout'))
        # Runs if user presses search
        elif request.form['Submit'] == "Submit":
            # Checks are used to determine what tables the flask app sends to the html template
            # Following lists are used to hold the players/teams user requested that don't exist
            badRequestPlayer = []
            badRequestTeam = []
            # Runs if player field isn't blank when submitted
            if request.form['player'] != "":
                # Separates players by comma and a space
                desired_players = request.form['player']
                player_list = desired_players.split(', ')
                try:
                    # Lists hold the players table
                    player_table = []
                    player_url = []
                    playerNameZip = []
                    playerCategoryZip = []
                    for player in player_list:
                        # Uses api to get player id and full name for each player in list
                        # The program runs even if you type part of a players name (Like Bron instead of LeBron James) so we still need to get their full name
                        player_dict = players.find_players_by_full_name(player)
                        player_id = player_dict[0]["id"]
                        player_name = player_dict[0]["full_name"]
                        active = player_dict[0]["is_active"]
                        playerFirst = player_dict[0]["first_name"].replace("'", "")[0:2].lower()
                        try:
                            playerLast = player_dict[0]["last_name"].replace("'", "")[0:5].lower()
                        except IndexError:
                            playerLast = player_dict[0]["last_name"].lower().replace("'", "")
                        if active:
                            player_basic = basic_df.loc[basic_df['Player'] == player_name].iloc[0]
                            player_advanced = advanced_df.loc[advanced_df['Player'] == player_name].iloc[0]

                            if player_basic['Pos'] in ["PG", "SG"]:
                                features = [player_basic['PTS'], player_basic['AST'], player_basic['STL'],
                                            player_advanced['DWS'], player_advanced['VORP']]
                                features = pandas.DataFrame([features])
                                scaled_features = scalerg.transform(features)
                                categorizing = kmg.predict(scaled_features)
                                role = ["Role Player", "Star Player", "Bench Warmer"]
                                matched_category = role[categorizing[0]]
                            elif player_basic['Pos'] in ["SF", "PF"]:
                                features = [player_basic['PTS'], player_basic['AST'], player_basic['STL'],
                                            player_advanced['DWS'], player_advanced['VORP']]
                                features = pandas.DataFrame([features])
                                scaled_features = scalerw.transform(features)
                                categorizing = kmw.predict(scaled_features)
                                role = ["Star Player", "Role Player", "Bench Warmer"]
                                matched_category = role[categorizing[0]]
                            elif player_basic['Pos'] == "C":
                                features = [player_basic['PTS'], player_basic['TRB'], player_basic['BLK'],
                                            player_advanced['DWS'], player_advanced['VORP']]
                                features = pandas.DataFrame([features])
                                scaled_features = scalerb.transform(features)
                                categorizing = kmb.predict(scaled_features)
                                role = ["Bench Warmer", "Star Player", "Role Player"]
                                matched_category = role[categorizing[0]]
                            else:
                                pass

                            data = pd.DataFrame({
                                "PastPPG": [player_basic['PTS']],
                                "PastRPG": [player_basic['TRB']],
                                "PastAPG": [player_basic['AST']],
                                "PastSPG": [player_basic['STL']],
                                "PastBPG": [player_basic['BLK']],
                                "PastAGE": [player_basic['Age']]
                            })
                            predict = xgb.predict(data[['PastPPG', 'PastRPG', 'PastAPG', 'PastSPG', 'PastBPG', 'PastAGE']])
                            newRow = pd.DataFrame({
                                'SEASON_ID': [str(season) + "-" + str(season + 1)[2:4]],
                                'TEAM_ABBREVIATION': [None],
                                'PLAYER_AGE': [player_basic['Age'] + 1],
                                'GP': [None],
                                'GS': [None],
                                'PTS': [str(round(predict[0][0], 1))],
                                'REB': [str(round(predict[0][1], 1))],
                                'AST': [str(round(predict[0][2], 1))],
                                'STL': [str(round(predict[0][3], 1))],
                                'BLK': [str(round(predict[0][4], 1))],
                                'FG_PCT': [None],
                                'FG3_PCT': [None],
                                'FT_PCT': [None]
                            })
                        # Uses player id to get the stats of the player as an object
                        player_info = playercareerstats.PlayerCareerStats(player_id=player_id)
                        # Converts object into a dataframe
                        playerdf = player_info.get_data_frames()[0]
                        # Dataframe only returns total pts, reb, and ast, so we need to calculate the avg per game
                        pts_avg = playerdf['PTS'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('PTS').round(1)
                        reb_avg = playerdf['REB'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('REB').round(1)
                        ast_avg = playerdf['AST'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('AST').round(1)
                        stl_avg = playerdf['STL'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('STL').round(1)
                        blk_avg = playerdf['BLK'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('BLK').round(1)
                        # Selects what stats to display in the html
                        playerselection = pandas.concat(
                            [playerdf[['SEASON_ID', 'TEAM_ABBREVIATION', 'PLAYER_AGE', 'GP', 'GS']], pts_avg, reb_avg,
                             ast_avg, stl_avg, blk_avg, playerdf[['FG_PCT', 'FG3_PCT', 'FT_PCT']]], axis=1)
                        # Adds a multilevel header with the player's name
                        if active:
                            playerCategoryZip.append(matched_category)
                            playerselection = pd.concat([playerselection, newRow])
                        else:
                            playerCategoryZip.append("Retired")
                        playerselection = pandas.concat([playerselection], keys=["Player History"], axis=1)
                        playerselection = playerselection.rename(columns={'SEASON_ID': 'YEAR', 'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE', 'FG_PCT': 'FG%', 'FG3_PCT': '3PT%', 'FT_PCT': 'FT%'})
                        # Converts dataframe into a html table and adds it to the list
                        player_table.append(playerselection.to_html(classes="table table-striped tableFont", index=False))
                        player_url.append(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerLast + playerFirst}01.jpg")
                        playerNameZip.append(player_name)
                # Runs if a player doesn't exist
                except IndexError:
                    player_table = []
                    player_url = []
                    playerNameZip = []
                    playerCategoryZip = []
                    # List keeps track of all players who exist
                    valid_players = []
                    for player in player_list:
                        try:
                            player_dict = players.find_players_by_full_name(player)
                            # Player_id used to trigger index error if player doesn't exist
                            player_id = player_dict[0]["id"]
                            # If index error doesn't occur, player is added to list of valid players
                            valid_players.append(player)
                        # If index error occurs, player is added to list of unknown players
                        except IndexError:
                            badRequestPlayer.append(player)
                    # Creates dataframe for each valid player (code reused from above)
                    for player in valid_players:
                        # Uses api to get player id and full name for each player in list
                        # The program runs even if you type part of a players name (Like Bron instead of LeBron James) so we still need to get their full name
                        player_dict = players.find_players_by_full_name(player)
                        player_id = player_dict[0]["id"]
                        player_name = player_dict[0]["full_name"]
                        active = player_dict[0]["is_active"]
                        playerFirst = player_dict[0]["first_name"].replace("'", "")[0:2].lower()
                        try:
                            playerLast = player_dict[0]["last_name"].replace("'", "")[0:5].lower()
                        except IndexError:
                            playerLast = player_dict[0]["last_name"].lower().replace("'", "")
                        playerUrl = f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerLast + playerFirst}01.jpg"
                        if active:
                            try:
                                player_basic = basic_df.loc[basic_df['Player'] == player_name].iloc[0]
                                player_advanced = advanced_df.loc[advanced_df['Player'] == player_name].iloc[0]

                                if player_basic['Pos'] in ["PG", "SG"]:
                                    features = [player_basic['PTS'], player_basic['AST'], player_basic['STL'],
                                                player_advanced['DWS'], player_advanced['VORP']]
                                    features = pandas.DataFrame([features])
                                    scaled_features = scalerg.transform(features)
                                    categorizing = kmg.predict(scaled_features)
                                    role = ["Role Player", "Star Player", "Bench Warmer"]
                                    matched_category = role[categorizing[0]]
                                elif player_basic['Pos'] in ["SF", "PF"]:
                                    features = [player_basic['PTS'], player_basic['AST'], player_basic['STL'],
                                                player_advanced['DWS'], player_advanced['VORP']]
                                    features = pandas.DataFrame([features])
                                    scaled_features = scalerw.transform(features)
                                    categorizing = kmw.predict(scaled_features)
                                    role = ["Star Player", "Role Player", "Bench Warmer"]
                                    matched_category = role[categorizing[0]]
                                elif player_basic['Pos'] == "C":
                                    features = [player_basic['PTS'], player_basic['TRB'], player_basic['BLK'],
                                                player_advanced['DWS'], player_advanced['VORP']]
                                    features = pandas.DataFrame([features])
                                    scaled_features = scalerb.transform(features)
                                    categorizing = kmb.predict(scaled_features)
                                    role = ["Bench Warmer", "Star Player", "Role Player"]
                                    matched_category = role[categorizing[0]]
                                else:
                                    pass

                                data = pd.DataFrame({
                                    "PastPPG": [player_basic['PTS']],
                                    "PastRPG": [player_basic['TRB']],
                                    "PastAPG": [player_basic['AST']],
                                    "PastSPG": [player_basic['STL']],
                                    "PastBPG": [player_basic['BLK']],
                                    "PastAGE": [player_basic['Age']]
                                })
                                predict = xgb.predict(data[['PastPPG', 'PastRPG', 'PastAPG', 'PastSPG', 'PastBPG', 'PastAGE']])
                                newRow = pd.DataFrame({
                                    'SEASON_ID': [str(season) + "-" + str(season + 1)[2:4]],
                                    'TEAM_ABBREVIATION': [None],
                                    'PLAYER_AGE': [player_basic['Age'] + 1],
                                    'GP': [None],
                                    'GS': [None],
                                    'PTS': [str(round(predict[0][0], 1))],
                                    'REB': [str(round(predict[0][1], 1))],
                                    'AST': [str(round(predict[0][2], 1))],
                                    'STL': [str(round(predict[0][3], 1))],
                                    'BLK': [str(round(predict[0][4], 1))],
                                    'FG_PCT': [None],
                                    'FG3_PCT': [None],
                                    'FT_PCT': [None]
                                })
                            except IndexError:
                                pass

                        # Uses player id to get the stats of the player as an object
                        player_info = playercareerstats.PlayerCareerStats(player_id=player_id)
                        # Converts object into a dataframe
                        playerdf = player_info.get_data_frames()[0]
                        # Dataframe only returns total pts, reb, and ast, so we need to calculate the avg per game
                        pts_avg = playerdf['PTS'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('PTS').round(1)
                        reb_avg = playerdf['REB'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('REB').round(1)
                        ast_avg = playerdf['AST'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('AST').round(1)
                        stl_avg = playerdf['STL'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('STL').round(1)
                        blk_avg = playerdf['BLK'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('BLK').round(1)
                        # Selects what stats to display in the html
                        playerselection = pandas.concat(
                            [playerdf[['SEASON_ID', 'TEAM_ABBREVIATION', 'PLAYER_AGE', 'GP', 'GS']], pts_avg, reb_avg,
                             ast_avg, stl_avg, blk_avg, playerdf[['FG_PCT', 'FG3_PCT', 'FT_PCT']]], axis=1)
                        playerselection = playerselection.rename(columns={'SEASON_ID': 'YEAR', 'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE', 'FG_PCT': 'FG%', 'FG3_PCT': '3PT%', 'FT_PCT': 'FT%'})
                        # Adds a multilevel header with the player's name
                        if active:
                            try:
                                playerCategoryZip.append(matched_category)
                                playerselection = pd.concat([playerselection, newRow])
                            except UnboundLocalError:
                                playerCategoryZip.append("Free Agent")
                        else:
                            playerCategoryZip.append("Retired")
                        playerselection = pandas.concat([playerselection], keys=["Player History"], axis=1)
                        # Converts dataframe into a html table and adds it to the list
                        player_table.append(playerselection.to_html(classes="table table-striped tableFont", index=False))
                        player_url.append(playerUrl)
                        playerNameZip.append(player_name)
            # Runs if team field isn't blank when submitted
            if request.form['team'] != "":
                # Separates teams by comma and a space
                desired_teams = request.form['team']
                team_list = desired_teams.split(', ')
                try:
                    # Team table holds the teams dataframe
                    team_table = []
                    for team in team_list:
                        team_dict = teams.find_teams_by_full_name(team)
                        # Like the player section, we need the full name since the program accepts partial names (like Dal for Dallas)
                        team_name = team_dict[0]["full_name"]
                        team_id = team_dict[0]["id"]
                        # Returns team roster information as an object
                        team_roster = commonteamroster.CommonTeamRoster(team_id=team_id)
                        # Converts object into a dataframe
                        teamdf = team_roster.get_data_frames()
                        # Selects specific columns to display to user
                        teamselection = teamdf[0][
                            ['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'AGE', 'EXP', 'SCHOOL', 'HOW_ACQUIRED']]
                        teamselection = pandas.concat([teamselection], keys=[team_name], axis=1)
                        team_table.append(teamselection.to_html(classes='table table-striped', index=False))
                # Runs if one of the teams doesn't exist
                except IndexError:
                    team_table = []
                    valid_teams = []
                    for team in team_list:
                        try:
                            team_dict = teams.find_teams_by_full_name(team)
                            # Team_id is used to trigger an index error if name doesn't exist
                            team_id = team_dict[0]["id"]
                            valid_teams.append(team)
                        except IndexError:
                            badRequestTeam.append(team)
                    # Code reused from above
                    for team in valid_teams:
                        team_dict = teams.find_teams_by_full_name(team)
                        team_name = team_dict[0]["full_name"]
                        team_id = team_dict[0]["id"]
                        team_roster = commonteamroster.CommonTeamRoster(team_id=team_id)
                        teamdf = team_roster.get_data_frames()
                        teamselection = teamdf[0][
                            ['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'AGE', 'EXP', 'SCHOOL', 'HOW_ACQUIRED']]
                        teamselection = pandas.concat([teamselection], keys=[team_name], axis=1)
                        team_table.append(teamselection.to_html(classes='table table-striped', index=False))

            # Returns search.html if no valid players were typed
            # Returns dataTable.html if at least one valid player or team was typed in
            if request.form['player'] == "" and request.form['team'] == "":
                return render_template('search.html', save=flask_login.current_user.id)
            elif bool(request.form['player'] == "") != bool(request.form['team'] == ""):
                try:
                    if len(player_table) != 0:
                        return render_template('dataTable.html', save=flask_login.current_user.id,
                                               playertable=zip(player_table, player_url, playerNameZip, playerCategoryZip), badPlayer=badRequestPlayer)
                    else:
                        return render_template('search.html', save=flask_login.current_user.id,
                                               badPlayer=badRequestPlayer)
                except UnboundLocalError:
                    if len(team_table) != 0:
                        return render_template('dataTable.html', save=flask_login.current_user.id, teamtable=team_table,
                                               badTeam=badRequestTeam)
                    else:
                        return render_template('search.html', save=flask_login.current_user.id, badTeam=badRequestTeam)
            elif len(player_table) == 0 and len(team_table) == 0:
                return render_template('search.html', save=flask_login.current_user.id, badTeam=badRequestTeam,
                                       badPlayer=badRequestPlayer)
            else:
                return render_template('dataTable.html', save=flask_login.current_user.id, playertable=zip(player_table, player_url, playerNameZip, playerCategoryZip),
                                       teamtable=team_table, badPlayer=badRequestPlayer, badTeam=badRequestTeam)
        # Returns user to search.html if return to search button is pressed
        elif request.form['Submit'] == "return":
            return render_template('search.html', save=flask_login.current_user.id)
    # Returns search.html if method is GET instead of POST
    else:
        return render_template('search.html', save=flask_login.current_user.id)


# Runs app in debug mode
if __name__ == "__main__":
    app.run(debug=True)
