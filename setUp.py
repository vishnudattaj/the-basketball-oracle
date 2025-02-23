import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor
import joblib

#I downloaded the datasets manually to train the model, I plan on automating the downloading process
advanced_stats_df = pd.read_csv("Advanced.csv")
per_game_stats_df = pd.read_csv("Players_Per_Game.csv")
shooting_stats_df = pd.read_csv("Player_Shooting.csv")

# Merges the dataframes, removes all rows with blank spaces, removes all data before 2004, and removes birth_year since only some players had it
combined_df = pd.merge(advanced_stats_df, per_game_stats_df, on=['seas_id', 'season', 'player_id', 'player', 'birth_year', 'pos', 'age', 'experience', 'lg', 'tm', 'g'])
combined_df = pd.merge(combined_df, shooting_stats_df, on=['seas_id', 'season', 'player_id', 'player', 'birth_year', 'pos', 'age', 'experience', 'lg', 'tm', 'g'])
combined_df.drop(columns=['birth_year'], inplace=True)
combined_df = combined_df[combined_df['season'] >= 1980]

combined_df.dropna(inplace=True)

# Made dataframes based on position
combined_guard = combined_df[combined_df['pos'] == ("PG" or "SG")]
combined_wing = combined_df[combined_df['pos'] == ("SF" or "PF")]
combined_big = combined_df[combined_df['pos'] == "C"]

# Selected features per position
guardFeatures = ['pts_per_game', 'ast_per_game', 'stl_per_game', 'dws', 'vorp']
wingFeatures = ['pts_per_game', 'ast_per_game', 'stl_per_game', 'dws', 'vorp']
bigFeatures = ['pts_per_game', 'trb_per_game', 'blk_per_game', 'dws', 'vorp']

# Scales the features to optimize the clusters
scaler = MinMaxScaler()
scaled_features = scaler.fit_transform(combined_guard[guardFeatures])

# Creates the kmeans model
km = KMeans(n_clusters=3, random_state=42)
y_predicted = km.fit_predict(scaled_features)

# Downloads model and scaler as a file
joblib.dump(km, 'kmeans_model_guard.sav')
joblib.dump(scaler, 'scaler_guard.gz')

# Scales the features to optimize the clusters
scaler = MinMaxScaler()
scaled_features = scaler.fit_transform(combined_wing[wingFeatures])

# Creates the kmeans model
km = KMeans(n_clusters=3, random_state=42)
y_predicted = km.fit_predict(scaled_features)

# Downloads model and scaler as a file
joblib.dump(km, 'kmeans_model_wing.sav')
joblib.dump(scaler, 'scaler_wing.gz')

# Scales the features to optimize the clusters
scaler = MinMaxScaler()
scaled_features = scaler.fit_transform(combined_big[bigFeatures])

# Creates the kmeans model
km = KMeans(n_clusters=3, random_state=42)
y_predicted = km.fit_predict(scaled_features)

# Downloads model and scaler as a file
joblib.dump(km, 'kmeans_model_big.sav')
joblib.dump(scaler, 'scaler_big.gz')

combined_df['PastPPG'] = combined_df.groupby('player')['pts_per_game'].shift(-1)
combined_df['PastRPG'] = combined_df.groupby('player')['trb_per_game'].shift(-1)
combined_df['PastAPG'] = combined_df.groupby('player')['ast_per_game'].shift(-1)
combined_df['PastSPG'] = combined_df.groupby('player')['stl_per_game'].shift(-1)
combined_df['PastBPG'] = combined_df.groupby('player')['blk_per_game'].shift(-1)
combined_df['PastAGE'] = combined_df.groupby('player')['age'].shift(-1)

combined_df.dropna(inplace=True)

X = combined_df[['PastPPG', 'PastRPG', 'PastAPG', 'PastSPG', 'PastBPG', 'PastAGE']]
y = combined_df[['pts_per_game', 'trb_per_game', 'ast_per_game', 'stl_per_game', 'blk_per_game']]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=5)

model = MultiOutputRegressor(XGBRegressor(learning_rate=0.1, max_depth=3))

model.fit(X_train, y_train)

joblib.dump(model, filename='statPrediction.sav')