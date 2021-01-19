import numpy as np
import pandas as pd
import xgboost as xgb
import os

winner_model = None
spread_model = None
totals_model = None
game_df = None
predict_df = None

def load_models():
    global winner_model
    winner_model = xgb.Booster({'nthread':4}) #init model
    winner_model.load_model(os.path.abspath('../marchmadness2020/models/winners.model')) # load data
    print('Winner model loaded')

    global spread_model
    spread_model = xgb.Booster({'nthread':4}) #init model
    spread_model.load_model(os.path.abspath('../marchmadness2020/models/spreads.model')) # load data
    print('Spread model loaded')

    global totals_model
    totals_model = xgb.Booster({'nthread':4}) #init model
    totals_model.load_model(os.path.abspath('../marchmadness2020/models/totals.model')) # load data
    print('Totals model loaded')

def load_data():
    global game_df
    game_df = pd.read_csv(os.path.abspath('../marchmadness2020/test/game.csv'))
    game_df = game_df.iloc[:, :5]

def format_data(wTeamId, lTeamId):
    # Find number of wins for each team in each season
    wNumWins = game_df[game_df['WTeamID'] == wTeamId].count()['WTeamID']
    lNumWins = game_df[game_df['WTeamID'] == lTeamId].count()['WTeamID']

    # Find number of losses for each team
    wNumLosses = game_df[game_df['LTeamID'] == wTeamId].count()['LTeamID']
    lNumLosses = game_df[game_df['LTeamID'] == lTeamId].count()['LTeamID']

    global predict_df
    predict_df = pd.DataFrame(data=
                            {
                                'WTeamID': wTeamId,
                                'LTeamID': lTeamId,
                                'WNumWins': wNumWins,
                                'LNumWins': lNumWins,
                                'WNumLosses': wNumLosses,
                                'LNumLosses': lNumLosses
                            }, index=[0])

    # Find win percentage for each team
    predict_df['WWinPercentage'] = predict_df['WNumWins'] / (predict_df['WNumWins'] + predict_df['WNumLosses'])
    predict_df['LWinPercentage'] = predict_df['LNumWins'] / (predict_df['LNumWins'] + predict_df['LNumLosses'])

    # Find average win score
    predict_df['WAvgWinScore'] = game_df[game_df['WTeamID'] == wTeamId].mean()['WScore']
    predict_df['LAvgWinScore'] = game_df[game_df['WTeamID'] == lTeamId].mean()['WScore'] 

    # Find average loss score
    predict_df['WAvgLossScore'] = game_df[game_df['LTeamID'] == wTeamId].mean()['LScore']
    predict_df['LAvgLossScore'] = game_df[game_df['LTeamID'] == lTeamId].mean()['LScore']

    # Find Average Win Margin
    predict_df['WAvgWinMargin'] = game_df[game_df['WTeamID'] == wTeamId].mean()['WScore'] - game_df[game_df['WTeamID'] == wTeamId].mean()['LScore']
    predict_df['LAvgWinMargin'] = game_df[game_df['WTeamID'] == lTeamId].mean()['WScore'] - game_df[game_df['WTeamID'] == lTeamId].mean()['LScore']

    # Find Average Loss Margin
    predict_df['WAvgLossMargin'] = game_df[game_df['LTeamID'] == wTeamId].mean()['WScore'] - game_df[game_df['LTeamID'] == wTeamId].mean()['LScore']
    predict_df['LAvgLossMargin'] = game_df[game_df['LTeamID'] == lTeamId].mean()['WScore'] - game_df[game_df['LTeamID'] == lTeamId].mean()['LScore']

    # Find Strength of Schedule
    predict_df['WSOS'] = (game_df[game_df['WTeamID'] == wTeamId].mean()['OppWinPercentage'] * wNumWins + game_df[game_df['LTeamID'] == wTeamId].mean()['OppWinPercentage'] * wNumLosses) / (wNumWins + wNumLosses)
    predict_df['LSOS'] = (game_df[game_df['WTeamID'] == lTeamId].mean()['OppWinPercentage'] * lNumWins + game_df[game_df['LTeamID'] == lTeamId].mean()['OppWinPercentage'] * lNumLosses) / (lNumWins + lNumLosses)

    # Find Adjusted Win Percentage
    predict_df['WAdjustedWinPercentage'] = predict_df['WWinPercentage'] * predict_df['WSOS']
    predict_df['LAdjustedWinPercentage'] = predict_df['LWinPercentage'] * predict_df['LSOS']

    # Subtract relative columns (WNumWins - LNumWins, WAvgWinMargin - LAvgWinMargin, etc.)
    predict_df['NumWinsDifference'] = predict_df['WNumWins'] - predict_df['LNumWins']
    predict_df['NumLossesDifference'] = predict_df['WNumLosses'] - predict_df['LNumLosses']
    predict_df['AvgWinScoreDifference'] = predict_df['WAvgWinScore'] - predict_df['LAvgWinScore']
    predict_df['AvgLossScoreDifference'] = predict_df['WAvgLossScore'] - predict_df['LAvgLossScore']
    predict_df['AvgWinMarginDifference'] = predict_df['WAvgWinMargin'] - predict_df['LAvgWinMargin']
    predict_df['AvgLossMarginDifference'] = predict_df['WAvgLossMargin'] - predict_df['LAvgLossMargin']
    predict_df['WinPercentDifference'] = predict_df['WWinPercentage'] - predict_df['LWinPercentage']

    # Drop Team IDs
    predict_df = predict_df.drop(['WTeamID', 'LTeamID'], axis=1)

    # IMPORTANT: The column names must be in the same order as the model!
    cols = predict_df.columns.tolist()
    predict_df = predict_df[[cols[0]] + [cols[2]] + [cols[4]] + [cols[6]] + [cols[8]] + [cols[10]] + [cols[12]] + [cols[14]] + [cols[16]] + [cols[1]] + [cols[3]] + [cols[5]] + [cols[7]] + [cols[9]] + [cols[11]] + [cols[13]] + [cols[15]] + [cols[17]] + cols[18:]]

def predict():
    d_test = xgb.DMatrix(predict_df)

    pred = winner_model.predict(d_test)
    print("Predicted Winner (1 for W team, 0 for L team): ", pred[0])

    pred = spread_model.predict(d_test)
    print("Predicted Spread: (positive for W team, negative for L team)", pred[0], end='\n'*2)