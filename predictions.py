import pandas as pd
import numpy as np
from odds import calculate_odds


def run_predictions(week, match_stats, standings):
    sims_to_run = 100000
    df = pd.DataFrame(
        columns=["week", "home_team", "away_team", "home_wins", "away_wins", "draws", "home_score", "away_score",
                 "home_odds", "away_odds", "draw_odds"])
    # only use games before the game_week we want to predict
    game_week = int(week)
    historical = match_stats.loc[match_stats["wk"] < game_week]
    # make sure we only use games that have valid scores
    historical = historical.loc[match_stats["home_score"] > -1]

    # get average home and away scores for entire competition
    home_avg = historical["home_score"].mean() * historical["home_expected_goals"].mean()
    away_avg = historical["away_score"].mean() * historical["away_expected_goals"].mean()

    # games to predict
    to_predict = match_stats.loc[match_stats["wk"] == game_week]
    # loop through predicting games
    another_i = 1

    for i in to_predict.index:
        home_team = to_predict.loc[i, "home_team"]
        away_team = to_predict.loc[i, "away_team"]
        home_team_id = to_predict.loc[i, "home_id"]
        away_team_id = to_predict.loc[i, "away_id"]

        # average goals scored and goals conceded for home team
        home_team_exp_goals_for = historical.loc[match_stats["home_id"] == home_team_id, "home_expected_goals"].mean()
        home_team_exp_goals_against = historical.loc[match_stats["home_id"] == home_team_id, "away_expected_goals"].mean()

        # average goals scored and goals conceded for away team
        away_team_exp_goals_for = historical.loc[match_stats["away_id"] == away_team_id, "away_expected_goals"].mean()
        away_team_exp_goals_against = historical.loc[match_stats["away_id"] == away_team_id, "home_expected_goals"].mean()

        home_team_expected_to_actual_for = standings.loc[standings["team_id"] == home_team_id, "goals_for"].sum() / standings.loc[
            standings["team_id"] == home_team_id, "xg_for"].sum()
        home_team_expected_to_actual_against = standings.loc[standings["team_id"] == home_team_id, "goals_against"].sum() / \
                                               standings.loc[standings["team_id"] == home_team_id, "xg_against"].sum()

        away_team_expected_to_actual_for = standings.loc[standings["team_id"] == away_team_id, "goals_for"].sum() / standings.loc[
            standings["team_id"] == away_team_id, "xg_for"].sum()
        away_team_expected_to_actual_against = standings.loc[standings["team_id"] == away_team_id, "goals_against"].sum() / \
                                               standings.loc[standings["team_id"] == away_team_id, "xg_against"].sum()

        # calculate home and away offense and defense strength
        home_team_offense_strength = (home_team_exp_goals_for * home_team_expected_to_actual_for) / home_avg
        home_team_defense_strength = (home_team_exp_goals_against * home_team_expected_to_actual_against) / away_avg

        away_team_offense_strength = (away_team_exp_goals_for * away_team_expected_to_actual_for) / away_avg
        away_team_defense_strength = (away_team_exp_goals_against * away_team_expected_to_actual_against) / home_avg

        home_team_expected_goals = home_team_offense_strength * away_team_defense_strength * home_avg
        away_team_expected_goals = away_team_offense_strength * home_team_defense_strength * away_avg

        home_team_poisson = np.random.poisson(home_team_expected_goals, sims_to_run)
        away_team_poisson = np.random.poisson(away_team_expected_goals, sims_to_run)

        home_wins = np.sum(home_team_poisson > away_team_poisson) / sims_to_run * 100
        away_wins = np.sum(away_team_poisson > home_team_poisson) / sims_to_run * 100
        draws = np.sum(home_team_poisson == away_team_poisson) / sims_to_run * 100

        home_score_actual = to_predict.loc[i, "home_score"]
        away_score_actual = to_predict.loc[i, "away_score"]

        home_odds = calculate_odds(home_wins, 'favorite') if home_wins > 50 else calculate_odds(home_wins, 'dog')
        away_odds = calculate_odds(away_wins, 'favorite') if away_wins > 50 else calculate_odds(away_wins, 'dog')
        draw_odds = calculate_odds(draws, 'favorite') if draws > 50 else calculate_odds(draws, 'dog')

        df.loc[another_i] = {
            "week": game_week,
            "home_team": home_team,
            "away_team": away_team,
            "home_wins": home_wins,
            "away_wins": away_wins,
            "draws": draws,
            "home_score": home_score_actual,
            "away_score": away_score_actual,
            "home_odds": home_odds,
            "away_odds": away_odds,
            "draw_odds": draw_odds
        }
        another_i = another_i + 1
    print(df)
    print('made it')
    return df