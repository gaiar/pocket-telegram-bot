# Copyright (C) 2016  Andrew Comminos <andrew@comminos.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sqlite3
import random
import re

class MarkovDatabase:
    def __init__(self, db_path):
        """Opens a new MarkovDatabase from the given SQLite path."""
        self.conn = sqlite3.connect(db_path)

        cur = self.conn.cursor()
        # Set up chains table.
        # word is NULL if this is node represents the end of a message.
        # last_word is NULL if the given word starts a new message.
        # While space inefficient, letting multiple rows serve as a frequency weight
        # is rather nice and simple.
        cur.execute("""CREATE TABLE IF NOT EXISTS chains (
                       user_id INTEGER NOT NULL,
                       word TEXT,
                       last_word TEXT)""")

        # Create a users table to be able to easily associate a name with an id.
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
                       user_id INTEGER NOT NULL PRIMARY KEY,
                       first_name TEXT NOT NULL,
                       last_name TEXT,
                       username TEXT)""")

        self.conn.commit()

    def get_user_details(self, username):
        """Returns a 3-tuple of user details, (uid, first_name, last_name),
        or None if the username was not found."""
        cur = self.conn.cursor()
        user_results = cur.execute("SELECT user_id,first_name,last_name from users WHERE username=?",
                                   (username,)).fetchall()
        if len(user_results) == 0:
            return None

        return user_results[0]

    def add_message(self, user, message):
        """Parses a markov chain of the given message and adds it to the
        database to be associated with the provided user. The user's
        information is also stored in the database as well."""

        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?)",
                    (user.id, user.first_name, user.last_name, user.username))

        # Currently ignores new lines and tabs, but does include punctuation
        words = re.findall('\S+', message)
        if len(words) == 0:
            return

        last_word = None
        # We append a "None" entry to the end in order to commit the terminating word.
        for word in words + [None]:
            cur.execute("""INSERT INTO chains VALUES (?,?,?)""", (user.id, word, last_word))
            last_word = word

        self.conn.commit()

    def generate_message(self, user, choose_func=random.choice):
        """Generates a message for the given user ID.
        If there is insuffient data for the provided user ID, returns None.
        If choose_func is not provided to select a preferred entry from a list of
        rows, random.choice is used for uniformity."""

        cur = self.conn.cursor()

        def next_word(word):
            """Returns the word after the provided word for the current user
            according to their markov chain."""
            # FIXME: For some reason, we can't select NULL columns using None.
            if word:
                options = cur.execute("SELECT word FROM chains WHERE (user_id=? AND last_word=?)",
                                      (user, unicode(last_word))).fetchall()
            else:
                options = cur.execute("SELECT word FROM chains WHERE (user_id=? AND last_word IS NULL)",
                                      (user,)).fetchall()
            if len(options) == 0:
                return None

            word, = choose_func(options)
            return word

        last_word = None
        while True:
            last_word = next_word(last_word)
            if last_word is None:
                break
            yield last_word

    def close(self):
        self.conn.close()