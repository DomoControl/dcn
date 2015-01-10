#!/usr/bin/python
import sqlite3


class Database:
    """Class to use Database SQLITE"""

    dbname = '/home/pi/dcn/db/db.sqlite'

    def __init__(self, dbname=dbname):
        self.database = dbname

    def connection(self):
        """Connection di Database"""
        return sqlite3.connect(self.database)

    def query(self, query, args=(), one=False):
        """Return query"""
        cur = self.connection()
        res = cur.execute(query, args)

        # a = cur.rowcount()
        if query.find('SELECT') > -1:
            rv = [dict((res.description[idx][0], value) for idx, value in enumerate(row)) for row in res.fetchall()]
            cur.close()
            return (rv[0] if rv else None) if one else rv
        elif query.find('INSERT') or query.find('UPDATE') or query.find('DELETE'):
            cur.commit()
            cur.close()

    def setForm(self, mode, data, table):
        if mode == 'UPDATE':
            if 'submit' in data:  # Delete key submit
                del data['submit']
            for key, value in data.iteritems():
                key = key.replace('[\'', ',')
                key = key.replace('\']', '')
                key = key.split(',')
                q = "SELECT %s FROM %s WHERE id=%s" % (key[1], table, key[0])
                res = self.query(q)
                if str(res[0][key[1]]) != str(value):
                    q = "UPDATE " + table + " SET %s = '%s' WHERE id=%s" \
                        % (key[1], value, key[0])
                    self.query(q)
