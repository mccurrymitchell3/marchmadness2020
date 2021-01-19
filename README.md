# marchmadness2020
Predictive analysis using historic NCAA basketball data

## Components
There are three models that predict the game winner, the spread, and the total points scored by both teams. Each model uses feature engineering and XGBoost to train.

There is a web scraper that reads scheduled game info for the present day from espn. This file then takes the data and runs the above models on it. It will provide the predictions in the command line.

## How To Run
Go to command line and run `py scraper.py`. The results will appear in the command line in real time as they are predicted.