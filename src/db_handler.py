"""
handle database operations
"""

import os
import json
import sqlite3
from sqlite3 import Error
from contextlib import contextmanager


DB_PATH = os.path.join(os.path.expanduser('~'), ".mnemo.db")
FETCH_QUERY = 'SELECT * FROM slack_calls'

# indexes
TMID = 1
TMNM = 2
CHID = 3
ACTK = 4
BTTK = 5


class DBHandler:
    """
    Provides endpoints to perform DB operations
    """
    def __init__(self):
        self._instantiate()

    def fetch(self):
        """
        gets all the rows of the table

        :return: list having all row data with above indexing scheme
        """
        try:
            with self._connect() as db_cur:
                db_cur.execute(FETCH_QUERY)
                return db_cur.fetchall()
        except Exception as err:
            print('Failed to fetch data')
            print(err)
            return None

    def remove(self, team_id):
        """
        removes entry with the given team id

        :param team_id: unique slack ID for the team
        :return: True if successful, False otherwise
        """
        del_query = """DELETE FROM slack_calls
                        WHERE indexed_team_id={team_id}
                        """.format(
            team_id=team_id
        )

        try:
            with self._connect() as db_cur:
                db_cur.execute(del_query)
                return True
        except Exception as err:
            print('Failed to delete for %s', team_id)
            print(err)
            return False

    def add(self, path_to_json):
        """
        create a new entry in the database table

        :param path_to_json: absolute path to JSON file
        :return: True if successful, False otherwise
        """
        with open(path_to_json, "r") as data_file:
            auth_data = json.load(data_file)

        auth_data = {
            'access_token': auth_data['access_token'],
            'bot_access_token': auth_data['bot']['bot_access_token'],
            'channel_id': auth_data['incoming_webhook']['channel_id'],
            'team_id': auth_data['team_id'],
            'team_name': auth_data['team_name']
        }
        try:
            with self._connect() as db_cur:
                cols = ', '.join('"{}"'.format(col) for col in auth_data.keys())
                vals = ', '.join('"{}"'.format(col) for col in auth_data.values())

                try:
                    command = """INSERT INTO "slack_calls"
                                                ({keys})
                                                VALUES ({values})""".format(
                        keys=cols,
                        values=vals
                    )
                    # print(command)
                    db_cur.execute(command)
                except Error as err:
                    print("Failed to insert data")
                    print(err)
                    raise Exception
        except Exception as err:
            print("Failed to add %s to database", auth_data['team_name'])
            print(err)
            return False

    def _instantiate(self):
        """
        Instantiate a db file with the required table(s)
        TO BE CALLED MANUALLY FROM WITHIN SCRIPT
        :return: None
        """
        print("creating database with table(s) at " + DB_PATH)

        with self._connect() as db_cur:

            # create disasters table
            db_cur.execute("""CREATE TABLE IF NOT EXISTS slack_calls (
                            id integer PRIMARY KEY ,
                            team_id text UNIQUE NOT NULL ,
                            team_name text ,
                            channel_id text UNIQUE NOT NULL ,
                            access_token text UNIQUE NOT NULL ,
                            bot_access_token text UNIQUE NOT NULL ,
                            );
            """)

            # indexing columns for faster access
            db_cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS indexed_team_id ON slack_calls (
                                team_id
                                );
            """)

    @staticmethod
    @contextmanager
    def _connect():
        """
        provides connection to the database
        :yields: Cursor to database
        :return: None
        """
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            yield conn.cursor()
            conn.commit()
            conn.close()
        except Error as err:
            print("Failed to connect to the database")
            print(err)
            raise Exception
