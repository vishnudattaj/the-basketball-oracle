# The Basketball Oracle

**The Basketball Oracle** is a dynamic NBA analytics website where users can explore standings, view live scores, inspect team rosters, analyze player careers, check boxscores, and most notably — predict player performance for the upcoming season using machine learning and RAG-powered search.

**Demo Video:** [Watch Here](https://youtu.be/LPEVSYnCYn8)  
**Website:** Coming Soon

*Best viewed on laptops with a screen resolution of 1920 x 1080.*

---

## How It’s Made

**Tech Stack:** Flask, Python, HTML, CSS, JavaScript

- Built using Flask with templated front-end rendering.
- Data from `nba_api` and ESPN’s hidden score APIs.
- Machine learning models (KMeans + XGBoost) predict player stats based on past performance.
- AI Search powered by **LangChain** and **Ollama**, trained on Wikipedia articles using Retrieval-Augmented Generation (RAG).

[Kaggle Dataset](https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats)  
[NBA API](https://github.com/swar/nba_api)

---

## AI Search Toggle

A smart toggle lets users switch between:

- **Stat Search:** Fast access to raw stats and career data using `nba_api`.
- **AI Search:** Ask natural language questions powered by a semantic RAG pipeline.

Example queries:
- *How did analytics change player scouting in the NBA?*
- *Has switch-heavy defense redefined what it means to be a ‘good defender’?*
- *Why was Luka Doncic traded?*

Input sanitization has been expanded to support natural phrasing, punctuation, and smart quotes.

---

## Usage Instructions

1. **Create an account / log in.**
2. Use the **AI Search Toggle** to switch between AI and Search Mode.
3. Navigate the **Scoreboard** or **Standings** to access team pages.
4. Click any team name to explore roster details.
5. Click any player name to explore their player card.
6. Dive into **Boxscores** for granular stats and game breakdowns.

---

## Features

- Player stat predictions (PTS, REB, AST, STL, BLK) via ML models.
- NBA standings and live scores.
- Team rosters and player physical info.
- Fast player lookup via Stat Search.
- Natural language Q&A via RAG-powered AI Search.
- Boxscores with game analysis.
- Toggle between dark/light modes.
- Regular vs. playoff stat views.
- Password-protected dashboard access.
- Typeahead search with predictive suggestions.
- Help button for guidance on navigation
- **PRI (Player Relevance Index):** Custom metric for cross-era player comparison.

---

## Optimization Note

Performance and layout are optimized for standard laptop resolutions and may not display correctly on mobile or alternative screen sizes.
