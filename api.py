from flask import Flask, request
from flask_restful import reqparse
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from predictions import run_predictions
import json
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, resources={r"/predict": {"origins": "http://localhost:8080"}})


def connect_to_db():
    conn = psycopg2.connect("host='all-them-stats.chure6gtnama.us-east-1.rds.amazonaws.com' port='5432' "
                            "dbname='stats_data' user='bundesstats' password='bundesstats'")
    return conn


@app.route('/standings', methods=['GET'])
def fetch_standings():

    req_league = request.get_json()['league']
    req_week = request.get_json()['week']
    conn = connect_to_db()
    select_statement = 'select * from standings_' + req_league
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(select_statement)
    standings_dict = cursor.fetchall()
    conn.commit()
    conn.close()
    return standings_dict, 200


@app.route('/predict', methods=['POST'])
@cross_origin(origin='localhost')
def fetch_prediction():
    req_league = request.get_json()['league']
    req_week = request.get_json()['week']

    conn = connect_to_db()
    select_match_stats_statement = 'select * from full_match_stats_' + req_league
    select_standings_statement = 'select * from standings_' + req_league
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(select_match_stats_statement)
    match_stats = pd.DataFrame(data=cursor.fetchall())
    cursor.execute(select_standings_statement)
    standings = pd.DataFrame(data=cursor.fetchall())
    conn.commit()
    conn.close()

    predictions = run_predictions(req_week, match_stats, standings)
    predictions_dict = predictions.to_json(orient='index')
    predictions_json = json.loads(predictions_dict)
    return predictions_json, 200


@app.after_request
def after_request_func(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    print('this ran')
    return response


if __name__ == "__main__":
    app.run()