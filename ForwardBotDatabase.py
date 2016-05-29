import sqlite3
import random
import re


class ForwardBotDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

        cur = self.conn.cursor()

        # Create a users table to be able to easily associate a name with an id.
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
                           user_id INTEGER NOT NULL PRIMARY KEY,
                           first_name TEXT NOT NULL,
                           last_name TEXT,
                           username TEXT,
                           type TEXT,
                           auth_token TEXT)""")

        self.conn.commit()

    def get_auth_token(self, user_id):
        cur = self.conn.cursor()
        user_results = cur.execute("SELECT auth_token FROM users WHERE user_id=?",
                                   (user_id,)).fetchall()

        if len(user_results) == 0:
            return None
        self.conn.commit()
        return user_results[0][0]

    def get_user_details(self, user_id):
        cur = self.conn.cursor()
        user_results = cur.execute("SELECT user_id,first_name,last_name,auth_token FROM users WHERE user_id=?",
                                   (user_id,)).fetchall()

        if len(user_results) == 0:
            return None
        self.conn.commit()
        user = {}
        user['first_name'] = user_results[0][1]
        user['user_id'] = user_results[0][0]
        user['last_name'] = user_results[0][2]
        user['auth_token'] = user_results[0][3]

        return user

    def add_user(self, user, auth_token=''):
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",
                    (user.id, user.first_name, user.last_name, user.username, user.type, auth_token))

        self.conn.commit()

    def update_user(self, user, auth_token):
        cur = self.conn.cursor()
        # UPDATE players SET user_name='steven', age=32 WHERE user_name='steven';
        cur.execute("UPDATE users SET auth_token=? WHERE user_id=?",
                    (auth_token, user.id))
        self.conn.commit()
        return

    def get_users(self):
        cur = self.conn.cursor()
        user_results = cur.execute("SELECT user_id,first_name,last_name,auth_token FROM users").fetchall()
        users = {}
        if len(user_results) == 0:
            return None
        else:
            for user in user_results:
                user_ = {}
                user_['first_name'] = user[1]
                user_['user_id'] = user[0]
                user_['last_name'] = user[2]
                user_['auth_token'] = user[3]
                users[user[0]] = user_
        return users

    def close(self):
        self.conn.close()
