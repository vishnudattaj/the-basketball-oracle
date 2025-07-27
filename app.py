import flask
from PIL import UnidentifiedImageError
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
import flask_login
from nba_api.stats.endpoints import playercareerstats, commonteamroster, leaguestandings
from nba_api.stats.static import players, teams
import joblib
import requests
from datetime import datetime, date
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import os
import json
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import traceback
from replace_accents import replace_accents_characters
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from io import StringIO
from langchain_chroma import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

llm = OllamaLLM(model="mistral:7b-instruct-v0.2-q4_0")

embedding_function = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"}
)

template_string = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

llmDB = Chroma(persist_directory="betterChroma", embedding_function=embedding_function)

load_dotenv()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    headers_enabled=True
)
# Sets Up The Flask App
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
# Sets up the login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
limiter.init_app(app)

class User(flask_login.UserMixin):
    pass


# Sets up the database
class LoginScreen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usernames = db.Column(db.String(100), unique=True, nullable=False)
    passwords = db.Column(db.Text, nullable=False)

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
yr = date.today().year
month = date.today().month

# Scrapes basketball reference, uses today's date to determine what season we are in right now
if month >= 11:
    basic = f"https://www.basketball-reference.com/leagues/NBA_{yr + 1}_per_game.html"
    advanced = f"https://www.basketball-reference.com/leagues/NBA_{yr + 1}_advanced.html"
    shooting = f"https://www.basketball-reference.com/leagues/NBA_{yr + 1}_shooting.html"
    season = yr + 1
else:
    basic = f"https://www.basketball-reference.com/leagues/NBA_{yr}_per_game.html"
    advanced = f"https://www.basketball-reference.com/leagues/NBA_{yr}_advanced.html"
    shooting = f"https://www.basketball-reference.com/leagues/NBA_{yr}_shooting.html"
    season = yr

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Requests the page based on the above urls
basic_page = requests.get(basic, headers=headers, timeout=5)
advanced_page = requests.get(advanced, headers=headers, timeout=5)
shooting_page = requests.get(shooting, headers=headers, timeout=5)

# Sets up beautiful soup object
basic_soup = BeautifulSoup(basic_page.content, "html.parser")
advanced_soup = BeautifulSoup(advanced_page.content, "html.parser")
shooting_soup = BeautifulSoup(shooting_page.content, "html.parser")

# Finds the table based on the id
basic_table = basic_soup.find(id='per_game_stats')
advanced_table = advanced_soup.find(id='advanced')
shooting_table = shooting_soup.find(id='shooting')

# Converts the table to a dataframe
basic_df = pd.read_html(StringIO(str(basic_table)))[0]
advanced_df = pd.read_html(StringIO(str(advanced_table)))[0]
shooting_df = pd.read_html(StringIO(str(shooting_table)))[0]

# Replaced all stats with a blank spot with 0 so I wouldn't have to remove some key nba players
basic_df.fillna(0, inplace=True)
advanced_df.fillna(0, inplace=True)
shooting_df.fillna(0, inplace=True)

shooting_df.columns = shooting_df.columns.droplevel(0)

totalDF = pd.merge(pd.merge(basic_df, advanced_df, on='Player'), shooting_df, on='Player')

metrics = ['PTS', 'AST', 'TRB', 'BLK', 'STL', 'TS%', 'WS', 'USG%', 'PER', 'G']
weights = np.array([0.3, 0.15, 0.15, 0.05, 0.05, 0.15, 0.1, 0.1, 0.1, 0.1])
weights = weights / np.sum(weights)

scaler = MinMaxScaler()
totalDF[metrics] = scaler.fit_transform(totalDF[metrics])

totalDF['Score'] = np.dot(totalDF[metrics], weights)
totalDF['Score'] = totalDF['Score'] * 10

totalDF = totalDF.drop_duplicates(subset='Player', keep='first')

totalDF = totalDF.sort_values(by='Score', ascending=False)

totalDF['Rank'] = np.arange(1, len(totalDF) + 1)

totalDF[['Rank', 'Player', 'Score']].to_excel('ranked_players.xlsx', index=False)


allPlayers = []

for player in players.get_players():
    allPlayers.append(player['full_name'])

allTeams = []

for team in teams.get_teams():
    allTeams.append(team['full_name'])

teams_df = pd.DataFrame(allTeams)
teams_df.to_json('static/data/teams.json', orient='values')

total_df = pd.DataFrame(allPlayers + allTeams)
total_df.to_json('static/data/total.json', orient='values')

with open('static/data/teams.json', 'r') as file:
    teamDictionary = json.load(file)

def generateChunk(messages):
    for chunk in llm.stream(messages):
        yield chunk

# 401 page if user tries to access material without logging in
@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401


# Loads a user in a session
@login_manager.user_loader
def user_loader(username):
    user_data = LoginScreen.query.filter_by(usernames=username).first()
    if not user_data:
        return None

    user = User()
    user.id = username
    return user


# Redirects user to login page when they log out
@app.route('/logout')
def logout():
    session.clear()
    flask_login.logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = LoginScreen.query.filter_by(usernames=username).first()

        if user_data:
            user_data = LoginScreen.query.filter_by(usernames=username).first()
            hashed_password = user_data.passwords if user_data else generate_password_hash("dummy", method="pbkdf2:sha256")
            if check_password_hash(hashed_password, password):
                user = User()
                user.id = username
                flask_login.login_user(user)
                return redirect(url_for('protected'))

            @limiter.limit("5 per 5 minutes")
            def failed_attempt():
                return render_template('login.html', error="Incorrect password")

            return failed_attempt()

        return render_template('login.html', error="User does not exist")

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
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            signin = LoginScreen(usernames=username, passwords=hashed_password)
            # Checks if username already exists
            if bool(LoginScreen.query.filter_by(usernames=username).first()):
                return render_template('signup.html', error="Username already exists")
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
            return render_template('signup.html', error="Passwords must match")
    else:
        return render_template('signup.html')


# App route for home page - Only accessible once you log in or create an account
@app.route('/protected', methods=['GET', 'POST'])
@flask_login.login_required
@limiter.limit("20 per minute")
def protected():
    # Runs when user clicks one of the two buttons
    if request.method == 'POST':
        submit_action = request.form.get('Submit')
        # Logs user out if log out button is clicked
        if submit_action == "Log Out":
            return redirect(url_for('logout'))
        # Runs if user presses search
        if submit_action == "Submit":
            if 'stats' in request.form:
                player_input = request.form['stats']
                # Validate input - check for valid characters
                try:
                    if player_input and re.match(r'^[\u00C0-\u024F\u1E00-\u1EFFa-zA-Z,\s]+$', player_input):
                        if player_input[-2] == ",":
                            flask.session['items'] = player_input[:-2]
                        else:
                            flask.session['items'] = player_input
                        return redirect(url_for('search'))
                except:
                    pass
                return render_template('search.html', save=flask_login.current_user.id,
                                           standings=standingsHTML(), scoreboard=scoreboardData(),
                                           top_players=PRI(), error="Invalid search input")
            elif 'ai' in request.form:
                advanced_input = request.form['ai']
                try:
                    if advanced_input and re.match(r'^[\u00C0-\u024F\u1E00-\u1EFF\w\s.,!?\'"“”‘’()\-–:;]+$', advanced_input):
                        results = llmDB.similarity_search_with_relevance_scores(advanced_input, k=20)
                        rerank_inputs = [
                            [advanced_input, doc.page_content + f"\n\nSource: {doc.metadata['title']}"]
                            for doc, _score in results
                        ]
                        rerank_scores = reranker.predict(rerank_inputs)
                        scored_passages = sorted(zip(results, rerank_scores), key=lambda x: x[1], reverse=True)

                        top_contexts = [
                            f"{doc.metadata['title']}:\n{doc.page_content}"
                            for ((doc, _), _score) in scored_passages[:7]
                        ]
                        context_text = "\n\n---\n\n".join(top_contexts)
                        chat_prompt = ChatPromptTemplate.from_template(template_string)
                        prompt_value = chat_prompt.invoke({"context": context_text, "question": advanced_input})
                        flask.session['messages'] = [str(m.content) for m in prompt_value.to_messages()]
                        flask.session['aiQuestion'] = advanced_input
                        return redirect(url_for('aiSearch'))
                except Exception as e:
                    print(e)
                    pass
                return render_template('search.html', save=flask_login.current_user.id,
                                       standings=standingsHTML(), scoreboard=scoreboardData(),
                                       top_players=PRI(), error="Invalid search input")

    # Returns search.html if method is GET instead of POST
    else:
        return render_template('search.html', save=flask_login.current_user.id, standings=standingsHTML(), scoreboard=scoreboardData(), top_players = PRI())

@app.route('/protected/ai', methods=['GET', 'POST'])
@flask_login.login_required
def aiSearch():
    advanced_input = flask.session.get('aiQuestion')
    return render_template('dataTable.html', save=flask_login.current_user.id, aiResponse=[advanced_input],
                           scoreboard=scoreboardData(), top_players=PRI())

@app.route('/stream_response')
def stream_response():
    messages = flask.session.get('messages')
    def generate():
        for chunk in generateChunk(messages):
            yield chunk
    return Response(stream_with_context(generate()), content_type='text/plain')

@app.route('/protected/search', methods=['GET', 'POST'])
@flask_login.login_required
def search():
    badRequestPlayer = []
    desired_players = flask.session['items']
    player_list = desired_players.split(', ')
    player_list = list(dict.fromkeys(player_list))
    try:
        # Lists hold the players table
        player_table = []
        player_url = []
        playerNameZip = []
        playerCategoryZip = []
        playerScore = []
        team_table = []
        team_url = []
        for player in player_list:
            if [player] in teamDictionary:
                team = player
                team_dict = teams.find_teams_by_full_name(team)
                team_abbreviation = team_dict[0]["abbreviation"]
                team_id = team_dict[0]["id"]
                team_roster = commonteamroster.CommonTeamRoster(team_id=team_id)
                teamdf = team_roster.get_data_frames()
                teamselection = teamdf[0][
                    ['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'AGE', 'EXP', 'SCHOOL',
                     'HOW_ACQUIRED']]
                teamselection = teamselection.rename(columns={'HOW_ACQUIRED': 'HOW ACQUIRED'})
                teamselection['HOW ACQUIRED'] = teamselection['HOW ACQUIRED'].apply(create_link_abbreviation_acquisition)
                teamselection['PLAYER'] = teamselection['PLAYER'].apply(player_link)
                teamselection = pd.concat([teamselection], keys=["Team Roster"], axis=1)
                team_table.append(teamselection.to_html(classes='table table-striped', index=False, escape=False))
                team_url.append(f'{team_abbreviation.lower()}.png')
            else:
                player = player.replace("\\", "")
                # Uses api to get player id and full name for each player in list
                # The program runs even if you type part of a players name (Like Bron instead of LeBron James) so we still need to get their full name
                player_dict = players.find_players_by_full_name(player)
                player_id = player_dict[0]["id"]
                player_name = player_dict[0]["full_name"]
                active = player_dict[0]["is_active"]
                if active:
                    newRow, matched_category, score = predictPlayer(player_name)
                # Uses player id to get the stats of the player as an object
                playerselection, playoffselection = createPlayerDf(player_id)  # Now unpacking both return values
                if active:
                    try:
                        playerScore.append(score)
                        playerCategoryZip.append(matched_category)
                        futurePredictions = pd.concat([newRow], keys=["Future Predictions"], axis=1)
                        futurePredictions = futurePredictions.rename(
                            columns={'SEASON_ID': 'YEAR', 'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE',
                                     'FG_PCT': 'FG%', 'FG3_PCT': '3PT%', 'FT_PCT': 'FT%'})
                        player_table.append({
                            'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                            'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                            'Predictions': 'Yes',
                            'Future Predictions': futurePredictions.to_html(classes="table table-striped tableFont", index=False)
                        })
                    except UnboundLocalError:
                        playerScore.append(False)
                        playerCategoryZip.append("Free Agent")
                        player_table.append({
                            'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                            'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                            'Predictions': 'No'
                        })
                    except ValueError:
                        playerScore.append(False)
                        playerCategoryZip.append("Free Agent")
                        player_table.append({
                            'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                            'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                            'Predictions': 'No'
                        })
                else:
                    playerScore.append(False)
                    playerCategoryZip.append("Retired")
                    player_table.append({
                        'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                        'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                        'Predictions': 'No'
                    })
                # Converts dataframe into a html table and adds it to the list
                playerNameZip.append(player_name)
                player_url.append(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png")
    # Runs if a player doesn't exist
    except (UnidentifiedImageError, IndexError, re.error) as e:
        player_table = []
        player_url = []
        playerNameZip = []
        playerCategoryZip = []
        playerScore = []
        team_table = []
        team_url = []
        # List keeps track of all players who exist
        valid_players = []
        for player in player_list:
            player = player.replace("\\", "")
            try:
                if [player] in teamDictionary:
                    valid_players.append(player)
                else:
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
            if [player] in teamDictionary:
                team = player
                team_dict = teams.find_teams_by_full_name(team)
                team_abbreviation = team_dict[0]["abbreviation"]
                team_id = team_dict[0]["id"]
                team_roster = commonteamroster.CommonTeamRoster(team_id=team_id)
                teamdf = team_roster.get_data_frames()
                teamselection = teamdf[0][
                    ['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'AGE', 'EXP', 'SCHOOL',
                     'HOW_ACQUIRED']]
                teamselection = teamselection.rename(columns={'HOW_ACQUIRED': 'HOW ACQUIRED'})
                teamselection['HOW ACQUIRED'] = teamselection['HOW ACQUIRED'].apply(create_link_abbreviation_acquisition)
                teamselection['PLAYER'] = teamselection['PLAYER'].apply(player_link)
                teamselection = pd.concat([teamselection], keys=["Team Roster"], axis=1)
                team_table.append(teamselection.to_html(classes='table table-striped', index=False, escape=False))
                team_url.append(f'{team_abbreviation.lower()}.png')
            else:
                # Uses api to get player id and full name for each player in list
                # The program runs even if you type part of a players name (Like Bron instead of LeBron James) so we still need to get their full name
                player_dict = players.find_players_by_full_name(player)
                player_id = player_dict[0]["id"]
                player_name = player_dict[0]["full_name"]
                active = player_dict[0]["is_active"]
                if active:
                    try:
                        newRow, matched_category, score = predictPlayer(player_name)
                    except IndexError:
                        pass

                # Uses player id to get the stats of the player as an object
                playerselection, playoffselection = createPlayerDf(player_id)  # Now unpacking both return values
                if active:
                    try:
                        playerScore.append(score)
                        playerCategoryZip.append(matched_category)
                        futurePredictions = pd.concat([newRow], keys=["Future Predictions"], axis=1)
                        futurePredictions = futurePredictions.rename(
                            columns={'SEASON_ID': 'YEAR', 'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE',
                                     'FG_PCT': 'FG%', 'FG3_PCT': '3PT%', 'FT_PCT': 'FT%'})
                        player_table.append({
                            'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                            'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                            'Predictions': 'Yes',
                            'Future Predictions': futurePredictions.to_html(classes="table table-striped tableFont", index=False)
                        })
                    except UnboundLocalError:
                        playerScore.append(False)
                        playerCategoryZip.append("Free Agent")
                        player_table.append({
                            'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                            'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                            'Predictions': 'No'
                        })
                    except ValueError:
                        playerScore.append(False)
                        playerCategoryZip.append("Free Agent")
                        player_table.append({
                            'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                            'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                            'Predictions': 'No'
                        })
                else:
                    playerScore.append(False)
                    playerCategoryZip.append("Retired")
                    player_table.append({
                        'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                        'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                        'Predictions': 'No'
                    })
                try:
                    playerNameZip.append(player_name)
                    player_url.append(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png")
                except UnidentifiedImageError:
                    badRequestPlayer.append(player)
    return render_template('dataTable.html', save=flask_login.current_user.id, playertable=zip(player_table, player_url, playerNameZip, playerCategoryZip, playerScore), teamtable=zip(team_table, team_url), badPlayer=badRequestPlayer, scoreboard=scoreboardData(), top_players = PRI())
def standingsHTML():
    standings = leaguestandings.LeagueStandings()
    standings_df = standings.get_data_frames()[0]
    standingsSelection = standings_df[
        ['TeamName', 'WINS', 'LOSSES', 'WinPCT', 'ConferenceGamesBack', 'L10', 'strCurrentStreak',
         'Conference']]
    standingsSelection = standingsSelection.rename(
        columns={'TeamName': 'Team', 'WINS': 'W', 'LOSSES': 'L', 'WinPCT': 'Win%',
                 'ConferenceGamesBack': 'GB', 'strCurrentStreak': 'Strk'})
    westStandings = standingsSelection.loc[standingsSelection['Conference'] == 'West']
    eastStandings = standingsSelection.loc[standingsSelection['Conference'] == 'East']
    westStandings = westStandings.drop(columns=['Conference']).reset_index(drop=True)
    eastStandings = eastStandings.drop(columns=['Conference']).reset_index(drop=True)
    westIcon = []
    eastIcon = []
    for team in westStandings['Team']:
        team_dict = teams.find_teams_by_full_name(team)
        team_abbreviation = team_dict[0]["abbreviation"]
        if team_abbreviation == 'NOP':
            team_abbreviation = 'NO'
        if team_abbreviation == 'UTA':
            team_abbreviation = 'UTAH'
            user_theme = session.get('user_theme', 'dark')
            if user_theme == "dark":
                westIcon.append(f"https://a.espncdn.com/i/teamlogos/nba/500-dark/scoreboard/{team_abbreviation}.png")
            else:
                westIcon.append(f"https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{team_abbreviation}.png")
        else:
            westIcon.append(f"https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{team_abbreviation}.png")
    for team in eastStandings['Team']:
        team_dict = teams.find_teams_by_full_name(team)
        team_abbreviation = team_dict[0]["abbreviation"]
        if team_abbreviation == 'NYK':
            team_abbreviation = 'ny'
        eastIcon.append(f"https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{team_abbreviation}.png")
    westStandings.insert(0, '', westIcon)
    eastStandings.insert(0, '', eastIcon)
    westStandings[''] = westStandings[''].apply(create_img_tag)
    eastStandings[''] = eastStandings[''].apply(create_img_tag)
    westStandings['Team'] = westStandings['Team'].apply(create_link)
    eastStandings['Team'] = eastStandings['Team'].apply(create_link)
    westStandings.index += 1
    eastStandings.index += 1
    return [westStandings.to_html(classes='table table-striped standingsTable', escape=False), eastStandings.to_html(classes='table table-striped standingsTable', escape=False)]

def create_img_tag(link):
    return f'<img src="{link}" width="30"/>'

def create_link(name):
    name = name.split(" ")
    return f'<a href="/protected/teams/{name[-1]}">{name[-1]}</a>'\

def create_link_full(name):
    return f'<a href="/protected/teams/{name}">{name}</a>'

def player_link(name):
    newName = name.replace(" ", "+")
    return f'<a href="/protected/players/{newName}">{name}</a>'
@app.route('/protected/players/<string:player>', methods=['GET', 'POST'])
@flask_login.login_required
def playerHTML(player):
    try:
        playerCategoryZip = []
        player_table = []
        playerNameZip = []
        player_url = []
        player = player.replace("+", " ")
        player_dict = players.find_players_by_full_name(player)
        player_id = player_dict[0]["id"]
        player_name = player_dict[0]["full_name"]
        active = player_dict[0]["is_active"]
        if active:
            newRow, matched_category, score = predictPlayer(player_name)
        # Uses player id to get the stats of the player as an object
        playerselection, playoffselection = createPlayerDf(player_id)  # Now unpacking both return values
        if active:
            try:
                playerCategoryZip.append(matched_category)
                futurePredictions = pd.concat([newRow], keys=["Future Predictions"], axis=1)
                futurePredictions = futurePredictions.rename(
                    columns={'SEASON_ID': 'YEAR', 'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE', 'FG_PCT': 'FG%',
                             'FG3_PCT': '3PT%', 'FT_PCT': 'FT%'})
                player_table.append({
                    'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                    'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                    'Predictions': 'Yes',
                    'Future Predictions': futurePredictions.to_html(classes="table table-striped tableFont", index=False)
                })
            except UnboundLocalError:
                playerCategoryZip.append("Free Agent")
                player_table.append({
                    'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                    'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                    'Predictions': 'No'
                })
            except ValueError:
                playerCategoryZip.append("Free Agent")
                player_table.append({
                    'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                    'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                    'Predictions': 'No'
                })
        else:
            playerCategoryZip.append("Retired")
            player_table.append({
                'Table': playerselection.to_html(classes="table table-striped tableFont", index=False, escape=False),
                'PlayoffTable': playoffselection.to_html(classes="table table-striped tableFont", index=False, escape=False) if not playoffselection.empty else None,
                'Predictions': 'No'
            })
        # Converts dataframe into a html table and adds it to the list
        playerNameZip.append(player_name)
        player_url.append(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png")
        return render_template('dataTable.html', save=flask_login.current_user.id, playertable=zip(player_table, player_url, playerNameZip, playerCategoryZip, [score]), scoreboard=scoreboardData(), top_players = PRI())
    except:
        traceback.print_exc()
        return redirect(url_for('protected'))

@app.route('/protected/teams/<string:team>', methods=['GET', 'POST'])
@flask_login.login_required
def teamHTML(team):
    try:
        team_dict = teams.find_teams_by_full_name(team)
        team_abbreviation = team_dict[0]["abbreviation"]
        team_id = team_dict[0]["id"]
        team_roster = commonteamroster.CommonTeamRoster(team_id=team_id)
        teamdf = team_roster.get_data_frames()
        teamselection = teamdf[0][
            ['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'AGE', 'EXP', 'SCHOOL', 'HOW_ACQUIRED']]
        teamselection = teamselection.rename(columns={'HOW_ACQUIRED': 'HOW ACQUIRED'})
        teamselection['PLAYER'] = teamselection['PLAYER'].apply(player_link)
        teamselection['HOW ACQUIRED'] = teamselection['HOW ACQUIRED'].apply(create_link_abbreviation_acquisition)
        teamselection = pd.concat([teamselection], keys=["Team Roster"], axis=1)
        team_table = teamselection.to_html(classes='table table-striped', index=False, escape=False)
        team_url = f'{team_abbreviation.lower()}.png'
        return render_template('dataTable.html', save=flask_login.current_user.id, teamtable=zip([team_table], [team_url]), scoreboard=scoreboardData(), top_players = PRI())
    except:
        return redirect(url_for('protected'))

def create_link_abbreviation_acquisition(string):
    if string:
        for abbreviation in string.split(" "):
            if abbreviation == abbreviation.upper() and len(abbreviation) == 3 and abbreviation.isalpha():
                team_dict = teams.find_team_by_abbreviation(abbreviation)
                team_name = team_dict['full_name']
                team_name = team_name.split(" ")
                string = string.split(abbreviation)
                return f'{string[0]}<a href="/protected/teams/{team_name[-1]}">{abbreviation}</a>{string[-1]}'
    return string

@app.route('/protected/games/<int:gameId>', methods=['GET', 'POST'])
@flask_login.login_required
def boxScore(gameId):
    url = f"https://cdn.espn.com/core/nba/boxscore?xhr=1&gameId={gameId}"
    response = requests.get(url).json()
    boxscore = pd.json_normalize(response['gamepackageJSON']['boxscore']['players'])
    team_table = []
    team_url = []
    team_name = []
    names = []
    for team in boxscore['team.shortDisplayName']:
        team_dict = teams.find_teams_by_full_name(team)
        fullName = team_dict[0]["full_name"]
        team_name.append(create_link(fullName))
        team_abbreviation = team_dict[0]["abbreviation"]
        team_url.append(f'{team_abbreviation.lower()}.png')
        names.append(create_link_full(fullName))

    teamIndex = 0
    for team in boxscore['statistics']:
        key = ['Starter'] + team[0]['names']
        starters = []
        bench = []
        dnp = []
        teamTotals = [names[teamIndex]]

        for athlete in team[0]['athletes']:
            displayName = player_link(athlete['athlete']['displayName'])
            if athlete['stats']:
                stats = [displayName] + athlete['stats']
                if athlete['starter']:
                    starters.append(stats)
                else:
                    bench.append(stats)
            else:
                stats = [displayName] + ['DNP'] + ['-' for _ in range(13)]
                dnp.append(stats)
            index = 1
            for stats in athlete['stats']:
                if len(teamTotals) < 15:
                    teamTotals.append(stats)
                else:
                    if "-" not in teamTotals[index] or teamTotals[index][0] == "-":
                        if stats != "-":
                            teamTotals[index] = str(int(teamTotals[index]) + int(stats))
                    else:
                        made = int(teamTotals[index].split("-")[0])
                        attempted = int(teamTotals[index].split("-")[1])
                        teamTotals[index] = str(made + int(stats.split("-")[0])) + "-" + str(attempted + int(stats.split("-")[1]))
                index += 1
        starters = sorted(starters, key=lambda x: x[key.index('MIN')], reverse=True)
        bench = sorted(bench, key=lambda x: x[key.index('MIN')], reverse=True)

        starters_df = pd.DataFrame(starters, columns=key)
        starters_df = pd.concat([starters_df], keys=[team_name[teamIndex]], axis=1)
        bench_key = ['Bench'] + team[0]['names']
        bench_df = pd.DataFrame(bench + dnp, columns=bench_key)
        total_key = ['Total'] + team[0]['names']
        total_df = pd.DataFrame([teamTotals], columns=total_key, index=[0])
        team_table.append(starters_df.to_html(classes='table table-striped', index=False, escape=False) + bench_df.to_html(
            classes='table table-striped', index=False, escape=False) + total_df.to_html(
            classes='table table-striped', index=False, escape=False))
        teamIndex += 1

    return render_template('dataTable.html', save=flask_login.current_user.id, boxscore=zip(team_table, team_url),
                           scoreboard=scoreboardData(), top_players = PRI())


@app.route('/update_theme', methods=['POST'])
def update_theme():
    try:
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request data: {request.data}")
        print(f"Request json: {request.json}")

        if not request.json:
            return jsonify({"error": "No JSON data received"}), 400

        theme_data = request.json
        theme = theme_data.get('theme')

        if not theme:
            return jsonify({"error": "Missing theme parameter"}), 400

        print(f"Theme received: {theme}")

        # Store the theme in the session
        session['user_theme'] = theme

        return jsonify({"status": "success", "theme": theme})

    except Exception as e:
        print(f"Error in update_theme: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/update_stats_mode', methods=['POST'])
def update_stats_mode():
    mode_data = request.json
    mode = mode_data.get('mode')

    # Store the stats mode in the session for the current user
    session['stats_mode'] = mode

    return jsonify({"status": "success", "mode": mode})

def scoreboardData():
    url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    response = requests.get(url).json()

    events = response.get("events", [])

    scoreboard = pd.DataFrame(events)

    gameId = []
    for id in scoreboard['id']:
        gameId.append({'id': id})

    scoreData = []
    dictIndex = 0
    home_away_list = ['Home', 'Away']
    for score in scoreboard['competitions']:
        scoreDict = gameId[dictIndex]
        home_away = 0
        gameType = score[0]['notes']
        series = score[0]['series']
        if series['type'] == 'playoff':
            series = series['summary']
        else:
            series = ""
        scoreDict['series'] = series
        if gameType:
            gameType = gameType[0]['headline']
            if "Play-In" in gameType:
                gameType = gameType[3:]
                scoreDict['gameType'] = gameType.split(" - ")[1] + gameType.split(" - ")[0]
            else:
                scoreDict['gameType'] = gameType.split(" - ")[0]
        else:
            scoreDict['gameType'] = "NBA"
        for team in score[0]['competitors']:
            teamName = team['team']['name']
            team_dict = teams.find_teams_by_full_name(teamName)
            team_abbreviation = team_dict[0]["abbreviation"]
            scoreDict[home_away_list[home_away] + ' Team'] = team_abbreviation
            scoreDict[home_away_list[home_away] + ' Link'] = teamName
            scoreDict[home_away_list[home_away] + ' Score'] = team['score']
            scoreDict[home_away_list[home_away] + ' Record'] = team['records'][0]['summary']
            if team_abbreviation == "UTA":
                team_abbreviation = 'UTAH'
                user_theme = session.get('user_theme', 'dark')
                if user_theme == "dark":
                    scoreDict[home_away_list[home_away] + ' Logo'] = f"https://a.espncdn.com/i/teamlogos/nba/500-dark/scoreboard/{team_abbreviation}.png"
                else:
                    scoreDict[home_away_list[home_away] + ' Logo'] = f"https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{team_abbreviation}.png"
            else:
                scoreDict[home_away_list[home_away] + ' Logo'] = team['team']['logo']
            home_away += 1
        dictIndex += 1
        scoreData.append(scoreDict)
    gameData = []
    dictIndex = 0
    for time in scoreboard['status']:
        scoreDict = scoreData[dictIndex]
        period = time['period']
        displayClock = time['displayClock']
        eventdate = time['type']['shortDetail']
        status = time['type']['state']
        if status == "pre":
            date_format = "%m/%d"
            today = datetime.strptime(f"{date.today().month}/{date.today().day}", date_format)
            gameDay = datetime.strptime(eventdate.split(" - ")[0], date_format)
            difference = gameDay - today
            if difference.days == 0:
                eventdate = "TODAY, " + eventdate.split(" - ")[1]
            if difference.days == 1:
                eventdate = "TOMORROW, " + eventdate.split(" - ")[1]
        scoreDict['Quarter'] = 'Q' + str(period)
        scoreDict['Clock'] = displayClock
        scoreDict['Date'] = eventdate
        scoreDict['Status'] = status
        gameData.append(scoreDict)
        dictIndex += 1
    if len(gameData) == 0:
        gameData.append({'Status': 'No Games Scheduled Today'})
    return gameData

def normalize_name(name):
    return re.sub(r'\.', '', name)

def predictPlayer(player_name):
    try:
        player_basic = basic_df[basic_df['Player'].apply(replace_accents_characters) == replace_accents_characters(player_name)]
        player_advanced = advanced_df[advanced_df['Player'].apply(replace_accents_characters) == replace_accents_characters(player_name)]
        player_shooting = shooting_df[shooting_df['Player'].apply(replace_accents_characters) == replace_accents_characters(player_name)]
        playerScore = totalDF[totalDF['Player'].apply(replace_accents_characters) == replace_accents_characters(player_name)]

        player_basic = player_basic.iloc[0]
        player_advanced = player_advanced.iloc[0]
        player_shooting = player_shooting.iloc[0]
        score = round(playerScore.iloc[0]['Score'], 2)

        if player_basic['Pos'] in ["PG", "SG"]:
            features = [player_basic['PTS'], player_basic['AST'], player_basic['STL'],
                        player_advanced['WS'], player_advanced['VORP']]
            features = pd.DataFrame([features])
            scaled_features = scalerg.transform(features)
            categorizing = kmg.predict(scaled_features)
            role = ["Role Player", "Star Player", "Bench Warmer"]
            matched_category = role[categorizing[0]]
        elif player_basic['Pos'] in ["SF", "PF"]:
            features = [player_basic['PTS'], player_basic['AST'], player_basic['STL'],
                        player_advanced['WS'], player_advanced['VORP']]
            features = pd.DataFrame([features])
            scaled_features = scalerw.transform(features)
            categorizing = kmw.predict(scaled_features)
            role = ["Role Player", "Bench Warmer", "Star Player"]
            matched_category = role[categorizing[0]]
        elif player_basic['Pos'] == "C":
            features = [player_basic['PTS'], player_basic['TRB'], player_basic['BLK'],
                        player_advanced['WS'], player_advanced['VORP']]
            features = pd.DataFrame([features])
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
            "PastMIN": [player_basic['MP']],
            "PastAGE": [player_basic['Age']],
            "PastTS%": [player_advanced['TS%']],
            "PastFTR": [player_advanced['FTr']],
            "PastPER": [player_advanced['PER']],
            "PastUSG": [player_advanced['USG%']],
            "PastAS%": [player_advanced['AST%']],
            "PastRB%": [player_advanced['TRB%']],
            "PastST%": [player_advanced['STL%']],
            "PastBK%": [player_advanced['BLK%']],
            "Past3PA": [player_basic['3PA']],
            "PastDIST": [player_shooting['Dist.']]
        })
        predict = xgb.predict(data[['PastPPG', 'PastRPG', 'PastAPG', 'PastSPG', 'PastBPG', 'PastMIN', 'PastAGE',
                                    'PastTS%', 'PastFTR', 'PastPER', 'PastUSG', 'PastAS%', 'PastRB%', 'PastST%',
                                    'PastBK%', 'Past3PA', 'PastDIST']])
        newRow = pd.DataFrame({
            'SEASON_ID': [str(season) + "-" + str(season + 1)[2:4]],
            'TEAM_ABBREVIATION': ['-'],
            'PLAYER_AGE': [player_basic['Age'] + 1],
            'GP': ['-'],
            'GS': ['-'],
            'PTS': [str(round(predict[0][0], 1))],
            'REB': [str(round(predict[0][1], 1))],
            'AST': [str(round(predict[0][2], 1))],
            'STL': [str(round(predict[0][3], 1))],
            'BLK': [str(round(predict[0][4], 1))],
            'FG_PCT': ['-'],
            'FG3_PCT': ['-'],
            'FT_PCT': ['-']
        })
        return newRow, matched_category, score
    except:
        traceback.print_exc()
        return None, "Free Agent"


def createPlayerDf(player_id):
    player_info = playercareerstats.PlayerCareerStats(player_id=player_id)
    # Converts object into a dataframe
    playerdf = player_info.get_data_frames()[0]
    playoffDF = player_info.get_data_frames()[2]

    # Process regular season stats
    pts_avg = playerdf['PTS'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('PTS').round(1)
    reb_avg = playerdf['REB'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('REB').round(1)
    ast_avg = playerdf['AST'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('AST').round(1)
    stl_avg = playerdf['STL'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('STL').round(1)
    blk_avg = playerdf['BLK'].fillna(0).div(playerdf['GP'].fillna(1)).to_frame('BLK').round(1)

    for index, row in playerdf.iterrows():
        if row['TEAM_ABBREVIATION'] != "TOT":
            abbreviation = row['TEAM_ABBREVIATION']
            team_dict = teams.find_team_by_abbreviation(abbreviation)
            if team_dict:
                teamName = team_dict["full_name"]
                playerdf.loc[index, 'TEAM_ABBREVIATION'] = create_link_abbreviation(teamName, abbreviation)

    playerselection = pd.concat(
        [playerdf[['SEASON_ID', 'TEAM_ABBREVIATION', 'PLAYER_AGE', 'GP', 'GS']], pts_avg, reb_avg,
         ast_avg, stl_avg, blk_avg, playerdf[['FG_PCT', 'FG3_PCT', 'FT_PCT']]], axis=1)
    playerselection = playerselection.rename(
        columns={'SEASON_ID': 'YEAR', 'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE', 'FG_PCT': 'FG%',
                 'FG3_PCT': '3PT%', 'FT_PCT': 'FT%'})
    playerselection = pd.concat([playerselection], keys=["Player History"], axis=1)

    # Process playoff stats in the same way
    playoff_pts_avg = playoffDF['PTS'].fillna(0).div(playoffDF['GP'].fillna(1)).to_frame('PTS').round(1)
    playoff_reb_avg = playoffDF['REB'].fillna(0).div(playoffDF['GP'].fillna(1)).to_frame('REB').round(1)
    playoff_ast_avg = playoffDF['AST'].fillna(0).div(playoffDF['GP'].fillna(1)).to_frame('AST').round(1)
    playoff_stl_avg = playoffDF['STL'].fillna(0).div(playoffDF['GP'].fillna(1)).to_frame('STL').round(1)
    playoff_blk_avg = playoffDF['BLK'].fillna(0).div(playoffDF['GP'].fillna(1)).to_frame('BLK').round(1)

    for index, row in playoffDF.iterrows():
        if row['TEAM_ABBREVIATION'] != "TOT":
            abbreviation = row['TEAM_ABBREVIATION']
            team_dict = teams.find_team_by_abbreviation(abbreviation)
            if team_dict:
                teamName = team_dict["full_name"]
                playoffDF.loc[index, 'TEAM_ABBREVIATION'] = create_link_abbreviation(teamName, abbreviation)

    playoffselection = pd.concat(
        [playoffDF[['SEASON_ID', 'TEAM_ABBREVIATION', 'PLAYER_AGE', 'GP', 'GS']], playoff_pts_avg, playoff_reb_avg,
         playoff_ast_avg, playoff_stl_avg, playoff_blk_avg, playoffDF[['FG_PCT', 'FG3_PCT', 'FT_PCT']]], axis=1)
    playoffselection = playoffselection.rename(
        columns={'SEASON_ID': 'YEAR', 'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE', 'FG_PCT': 'FG%',
                 'FG3_PCT': '3PT%', 'FT_PCT': 'FT%'})
    playoffselection = pd.concat([playoffselection], keys=["Playoff History"], axis=1)

    return playerselection, playoffselection

def create_link_abbreviation(name, abbreviation):
    name = name.split(" ")
    return f'<a href="/protected/teams/{name[-1]}">{abbreviation}</a>'

def PRI():
    playerName = []
    playerScore = []
    playerURL = []
    topDF = totalDF.head(10)
    for index, row in topDF.iterrows():
        playername = row['Player']
        playerName.append(player_link(row['Player']))
        playerScore.append(round(row['Score'], 2))
        player_dict = players.find_players_by_full_name(playername)
        player_id = player_dict[0]["id"]
        playerURL.append(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png")
    return list(zip(playerName, playerScore, playerURL))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                          error_code="404",
                          error_title="Page Not Found",
                          error_message="The page you are looking for doesn't exist or has been moved.",
                          current_year=datetime.now().year), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                          error_code="500",
                          error_title="Internal Server Error",
                          error_message="Something went wrong on our end. Please try again later.",
                          current_year=datetime.now().year), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors by extracting from headers"""
    error_message = "You have issued too many requests"
    if hasattr(e, 'description'):
        error_message = str(e.description)

    # Try to get retry-after from response headers
    rate_reset_seconds = 60  # Default
    if hasattr(e, 'get_response'):
        response = e.get_response()
        if 'Retry-After' in response.headers:
            try:
                rate_reset_seconds = int(response.headers['Retry-After'])
            except (ValueError, TypeError):
                pass

    return render_template('error.html',
                           error_code="429",
                           error_title="Rate Limit Exceeded",
                           rate_reset_seconds=rate_reset_seconds,
                           current_year=datetime.now().year), 429

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src 'self' https://cdnjs.cloudflare.com https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' https://cdn.nba.com https://a.espncdn.com; "
        "frame-ancestors 'none'; "
        "object-src 'none'"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/protected/pri', methods=['POST', 'GET'])
@flask_login.login_required
def priInfo():
    return render_template('pri.html', save=flask_login.current_user.id, scoreboard=scoreboardData(), top_players = PRI())

# Runs app in debug mode
if __name__ == '__main__':
    app.run(debug=True)
