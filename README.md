# The Basketball Oracle 🏀📊

The Basketball Oracle is the ultimate basketball website that allows users to view NBA standings, today's scores, team roster info, player career information, boxscores, and most importantly: player predictions for the next season.

**Link to Demo:** [Link](https://youtu.be/LPEVSYnCYn8)

**Link to Website:** COMING SOON

**Important Notice:** This website is optimized for use on a laptop with a screen resolution of 1920 x 1080. It may not display as intended on other resolutions, so for the best viewing experience, please adjust your screen resolution accordingly.

---

## How It's Made 🔧

**Tech Stack:** Flask, Python, HTML, CSS, JavaScript

The application was built using the Flask framework. It uses `nba_api` to access player data and team rosters, and utilizes ESPN's hidden APIs to access scoreboard data. HTML and CSS are used for rendering templates, while JavaScript is employed for displaying the scoreboard, implementing a password check feature, and adding a light-dark mode toggle.

To classify players into categories, I used KMeans clustering with scikit-learn. The testing and training data was sourced from Kaggle's datasets. For predicting future stats, I used XGBoost Regression to forecast points, rebounds, assists, steals, and blocks based on past performance data.

To expand functionality, a toggle has been added that switches between:

- **Stat Search:** The original player search feature using `nba_api` and predictive models.  
- **AI Search:** A question-answering feature powered by a RAG (Retrieval-Augmented Generation) pipeline trained on Wikipedia articles. This uses **LangChain** and **Ollama** to provide natural language responses to queries like "How many NBA championships did the Dallas Mavericks win?" or more basketball related questions such as "What is a 3 and d player?"

**Link to Dataset:** [Kaggle Dataset](https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats)

**NBA Data Source:** The player and team data is sourced from the [nba_api](https://github.com/swar/nba_api), a Python library that provides access to the NBA's official API.

---

## Usage 📚

To use the features, first, you need to **log in** or **create an account** if you don't already have one. After logging in:

- **AI Search Toggle:** Use the toggle to switch between **Stat Search** for quick player lookups and **AI Search** for conversational queries answered using Wikipedia-trained models.
- **Team Information:** You can click on any team name in the standings or scoreboard to view their **roster**, which also includes basic player information such as height and weight.
- **Scoreboard:** View the **live scores** of NBA games and click on the team names to see detailed roster information for each team playing today.
- **Boxscores:** Dive into the **boxscores** of NBA games to explore detailed statistics such as individual player performances, team comparisons, and game highlights.

---

## Features ✨

- **Player Stats & Predictions:** Access detailed player stats, including points, assists, rebounds, steals, and blocks. Predict future stats based on past performance using machine learning models.
- **NBA Standings:** View the current NBA standings, sorted by conference and division.
- **Today's Scores:** Stay up-to-date with live scores of today's NBA games.
- **Team Rosters:** Click on any team in the standings or scoreboard to view detailed information about the team's roster.
- **Stat Search:** Quickly search for any player to view their current and past seasonal performances.
- **AI Search Toggle:** Switch between **Stat Search** and **AI Search** to ask natural language questions like “What is LeBron James' best season?” or “Why was Luka Doncic traded?”
- **Boxscores:** Get a deeper look into game statistics, including individual player stats, team comparisons, and detailed game analysis.
- **Dark/Light Mode:** Switch between dark and light modes for a more personalized browsing experience.
- **Regular/Playoff Stats:** Switch between seeing regular and playoff stats for a better user experience.
- **Password Protection:** A secure password feature ensures only authorized users can access certain data or sections of the site.
- **Typeahead Search:** Quickly find what you're looking for with real-time search suggestions that show matching player names, teams, and stats as you type.
- **PRI:** A custom made metric created in order to effectively compare NBA players. Further information can be found by hovering over the word PRI anywhere within the website.
