# Basketball Oracle 🏀📊

Basketball Oracle is the ultimate basketball website that allows users to view NBA standings, today's scores, team roster info, player career information, and most importantly: player predictions for the next season.

**Link to Website:** COMING SOON

## How It's Made 🔧

**Tech Stack:** Flask, Python, HTML, CSS, JavaScript

The application was built using the Flask framework. It uses `nba_api` to access player data and team rosters, and utilizes ESPN's hidden APIs to access scoreboard data. HTML and CSS are used for rendering templates, while JavaScript is employed for displaying the scoreboard, implementing a password check feature, and adding a light-dark mode toggle.

To classify players into categories, I used KMeans clustering with scikit-learn. The testing and training data was sourced from Kaggle's datasets. For predicting future stats, I used XGBoost Regression to forecast points, rebounds, assists, steals, and blocks based on past performance data.

**Link to Dataset:** [Kaggle Dataset](https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats)

## Lessons Learned 📚

This project taught me how to create a Flask framework to display HTML templates. I also gained experience in web scraping using the BeautifulSoup and Requests libraries. Additionally, I learned the basics of machine learning, including testing and training data, using metrics such as scikit-learn's cross-validation score, and working with different models like KMeans and XGBoost. Furthermore, I improved my skills in creating visually appealing and functional HTML templates.
