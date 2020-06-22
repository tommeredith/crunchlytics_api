from flask import Flask
from flask_restful import Resource, Api, reqparse
import pandas as pd
import psycopg2
from psycopg2.extensions import AsIs
from psycopg2.extras import RealDictCursor
from predictions import run_predictions
import json

app = Flask(__name__)
api = Api(app)


# df = pd.read_csv('league_table_premier.csv')
# standings_dict = df.to_dict(orient='index')


def connect_to_db():
    conn = psycopg2.connect("host='all-them-stats.chure6gtnama.us-east-1.rds.amazonaws.com' port='5432' "
                            "dbname='stats_data' user='bundesstats' password='bundesstats'")
    return conn


class Standings(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("league")
        parser.add_argument("week")
        params = parser.parse_args()

        conn = connect_to_db()
        select_statement = 'select * from standings_' + params["league"]
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(select_statement)
        standings_dict = cursor.fetchall()
        conn.commit()
        conn.close()
        return standings_dict, 200


class Predictions(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("league")
        parser.add_argument("week")
        params = parser.parse_args()

        conn = connect_to_db()
        select_match_stats_statement = 'select * from full_match_stats_' + params["league"]
        select_standings_statement = 'select * from standings_' + params["league"]
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(select_match_stats_statement)
        match_stats = pd.DataFrame(data=cursor.fetchall())
        cursor.execute(select_standings_statement)
        standings = pd.DataFrame(data=cursor.fetchall())
        conn.commit()
        conn.close()

        predictions = run_predictions(params["week"], match_stats, standings)
        predictions_dict = predictions.to_json(orient='index')
        predictions_json = json.loads(predictions_dict)
        return predictions_json, 200


api.add_resource(Standings, '/standings/')
api.add_resource(Predictions, '/predict/')


if __name__ == "__main__":
    app.run(debug=True)