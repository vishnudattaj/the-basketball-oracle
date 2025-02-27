# Basketball Oracle 🏀📊

Basketball Oracle is the ultimate basketball website that allows users to view NBA standings, today's scores, team roster info, player career information, and most importantly: player predictions for the next season.

**Link to Website:** COMING SOON

---

## How It's Made 🔧

**Tech Stack:** Flask, Python, HTML, CSS, JavaScript

The application was built using the Flask framework. It uses `nba_api` to access player data and team rosters, and utilizes ESPN's hidden APIs to access scoreboard data. HTML and CSS are used for rendering templates, while JavaScript is employed for displaying the scoreboard, implementing a password check feature, and adding a light-dark mode toggle.

To classify players into categories, I used KMeans clustering with scikit-learn. The testing and training data was sourced from Kaggle's datasets. For predicting future stats, I used XGBoost Regression to forecast points, rebounds, assists, steals, and blocks based on past performance data.

**Link to Dataset:** [Kaggle Dataset](https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats)

**NBA Data Source:** The player and team data is sourced from the [nba_api](https://github.com/swar/nba_api), a Python library that provides access to the NBA's official API.

---

## Usage 📚

To use the features, first, you need to **log in** or **create an account** if you don't already have one. After logging in:

- **Player Search:** Use the search bar to type in the name of any NBA player to see their current stats and future predictions for the upcoming season.
- **Team Information:** You can click on any team name in the standings or scoreboard to view their **roster**, which also includes basic player information such as height and weight.
- **Scoreboard:** View the **live scores** of NBA games and click on the team names to see detailed roster information for each team playing today.

---

## Features ✨

- **Player Stats & Predictions:** Access detailed player stats, including points, assists, rebounds, steals, and blocks. Predict future stats based on past performance using machine learning models.
- **NBA Standings:** View the current NBA standings, sorted by conference and division.
- **Today's Scores:** Stay up-to-date with live scores of today's NBA games.
- **Team Rosters:** Click on any team in the standings or scoreboard to view detailed information about the team's roster.
- **Player Search:** Quickly search for any player to view their current and past performance.
- **Dark/Light Mode:** Switch between dark and light modes for a more personalized browsing experience.
- **Password Protection:** A secure password feature ensures only authorized users can access certain data or sections of the site.
