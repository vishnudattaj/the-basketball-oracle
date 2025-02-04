import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
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

# Made an Excel spreadsheet with each sheet being the players in the category
# Helped me see if the model was accurate or not (I tried a lot of combinations for the features)
combined_guard['Archetype'] = y_predicted

group_column = "Archetype"

grouped = combined_guard.groupby(group_column)

with pd.ExcelWriter("archetypeSeperatedGuard.xlsx", engine='openpyxl') as writer:
    for group_name, group_data in grouped:
        group_data.to_excel(writer, sheet_name='group' + str(group_name), index=False)

# Scales the features to optimize the clusters
scaler = MinMaxScaler()
scaled_features = scaler.fit_transform(combined_wing[wingFeatures])

# Creates the kmeans model
km = KMeans(n_clusters=3, random_state=42)
y_predicted = km.fit_predict(scaled_features)

# Downloads model and scaler as a file
joblib.dump(km, 'kmeans_model_wing.sav')
joblib.dump(scaler, 'scaler_wing.gz')

# Made an Excel spreadsheet with each sheet being the players in the category
# Helped me see if the model was accurate or not (I tried a lot of combinations for the features)
combined_wing['Archetype'] = y_predicted

group_column = "Archetype"

grouped = combined_wing.groupby(group_column)

with pd.ExcelWriter("archetypeSeperatedWing.xlsx", engine='openpyxl') as writer:
    for group_name, group_data in grouped:
        group_data.to_excel(writer, sheet_name='group' + str(group_name), index=False)

# Scales the features to optimize the clusters
scaler = MinMaxScaler()
scaled_features = scaler.fit_transform(combined_big[bigFeatures])

# Creates the kmeans model
km = KMeans(n_clusters=3, random_state=42)
y_predicted = km.fit_predict(scaled_features)

# Downloads model and scaler as a file
joblib.dump(km, 'kmeans_model_big.sav')
joblib.dump(scaler, 'scaler_big.gz')

# Made an Excel spreadsheet with each sheet being the players in the category
# Helped me see if the model was accurate or not (I tried a lot of combinations for the features)
combined_big['Archetype'] = y_predicted

group_column = "Archetype"

grouped = combined_big.groupby(group_column)

with pd.ExcelWriter("archetypeSeperatedBig.xlsx", engine='openpyxl') as writer:
    for group_name, group_data in grouped:
        group_data.to_excel(writer, sheet_name='group' + str(group_name), index=False)