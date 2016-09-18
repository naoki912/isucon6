from flask import Flask, request, jsonify, abort
import MySQLdb.cursors
import os
import html
import urllib
from gevent import monkey; monkey.patch_all()

app = Flask(__name__)

def dbh():
    if hasattr(request, 'db'):
        return request.db
    else:
        request.db = MySQLdb.connect(**{
            'host': 'localhost',
            'port':'3306',
            'user': 'root',
            'passwd': '',
            'db': 'isutar',
            'charset': 'utf8mb4',
            'cursorclass': MySQLdb.cursors.DictCursor,
            'autocommit': True,
        })
        cur = request.db.cursor()
        cur.execute("SET SESSION sql_mode='TRADITIONAL,NO_AUTO_VALUE_ON_ZERO,ONLY_FULL_GROUP_BY'")
        cur.execute('SET NAMES utf8mb4')
        return request.db

@app.teardown_request
def close_db(exception=None):
    if hasattr(request, 'db'):
        request.db.close()

@app.route("/initialize")
def get_initialize():
    cur = dbh().cursor()
    cur.execute('TRUNCATE star')
    return jsonify(status = 'ok')

@app.route("/stars")
def get_stars():
    cur = dbh().cursor()
    cur.execute('SELECT * FROM star WHERE keyword = %s', (request.args['keyword'], ))
    return jsonify(stars = cur.fetchall())

@app.route("/stars", methods=['POST'])
def post_stars():
    keyword = request.args.get('keyword', "")
    if keyword == None or keyword == "":
        keyword = request.form['keyword']

    origin = os.environ.get('ISUDA_ORIGIN', 'http://localhost:5000')
    url = "%s/keyword/%s" % (origin, urllib.parse.quote(keyword))
    try:
        urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        if e.status == 404:
            abort(404)
        else:
            raise

    cur = dbh().cursor()
    cur.execute('INSERT INTO star (keyword, user_name, created_at) VALUES (%s, %s, NOW())', (keyword, request.args.get('user', '', )))

    user = request.args.get('user', "")
    if user == None or user == "":
        user = request.form['user']

    cur.execute('INSERT INTO star (keyword, user_name, created_at) VALUES (%s, %s, '
'NOW())', (keyword, user))

    return jsonify(result = 'ok')

if __name__ == "__main__":
    app.run()
