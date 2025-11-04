# app.py - Movies SQLi + Admin login tampering CTF
from flask import Flask, render_template, request, jsonify, g, session, redirect, url_for
import sqlite3, os, time

DB = "database.db"
ADMIN_FLAG = "flag{SATYAM_INJECTION}"
SQLI_FLAG  = "flag{SATYAM_INJECTION}"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "ctf_movies_secret_change_me"

def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB, check_same_thread=False)
    return db

@app.teardown_appcontext
def close_db(e=None):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def init_db():
    if os.path.exists(DB):
        return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, secret_note TEXT)')
    cur.execute("INSERT INTO users (username,password,secret_note) VALUES (?,?,?)", ('bob','bobpass','hello')) 
    cur.execute("INSERT INTO users (username,password,secret_note) VALUES (?,?,?)", ('admin','adm1npass',ADMIN_FLAG))
    cur.execute('CREATE TABLE movies (id INTEGER PRIMARY KEY, title TEXT, description TEXT)')
    movies = [
        ('The Great CTF','An intentionally vulnerable movie entry.'),
        ('Escape Room','A puzzle movie.'),
        ('Null Pointer','Bug-themed thriller.'),
        ('Injection Impossible','SQLi starrer.'),
        ('Session of Secrets','Auth-themed drama.')
    ]
    cur.executemany("INSERT INTO movies (title,description) VALUES (?,?)", movies)
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/movies')
def movies():
    # render movies list page which links to /movie?movieID=#
    return render_template('movies.html')

@app.route('/movie')
def movie():
    # Vulnerable to SQL injection: movieID is inserted verbatim
    movieID = request.args.get('movieID','1')
    query = f"SELECT id, title, description FROM movies WHERE id = {movieID};"
    cur = get_db().cursor()
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        return f"DB error: {e}\n\nQuery: {query}", 500
    return jsonify({"query": query, "rows": rows, "note": SQLI_FLAG if 'secret_note' in str(rows) else ''})

@app.route('/login', methods=['GET','POST'])
def login():
    # login page for admin only; intentionally vulnerable to tampering
    if request.method == 'GET':
        return render_template('login.html')
    # Accept form-encoded or JSON body. If the request includes admin=true, bypass password check.
    username = request.form.get('username') or (request.json.get('username') if request.is_json else None)
    password = request.form.get('password') or (request.json.get('password') if request.is_json else None)
    # check for tampering field: JSON boolean admin:true or form field admin=true
    admin_flag = None
    if request.is_json:
        admin_flag = request.json.get('admin', None)
    else:
        # form values are strings; accept 'true' or '1'
        admin_flag = request.form.get('admin', None)
        if admin_flag is not None:
            admin_flag = admin_flag.lower() in ('1','true','yes','on')
    # Basic user lookup
    cur = get_db().cursor()
    cur.execute("SELECT username, password FROM users WHERE username=? LIMIT 1", (username,))
    row = cur.fetchone()
    if not row:
        return ("bad creds", 401)
    stored_password = row[1]
    # Normal login path
    if stored_password == password:
        session['user'] = username
        session['role'] = 'admin' if username == 'admin' else 'user'
        return jsonify({"msg":"login ok","user":username,"role":session['role']})
    # Vulnerable bypass: if request included admin=true, log in as admin for that username
    if admin_flag:
        session['user'] = username
        session['role'] = 'admin'
        return jsonify({"msg":"flag{SATYAM_AUTHENTICATION}","user":username,"role":"admin"})
    return ("bad creds", 401)

@app.route('/admin')
def admin():
    if session.get('role') == 'admin' or session.get('user') == 'admin':
        return jsonify({"msg":"welcome admin","flag": ADMIN_FLAG})
    return jsonify({"error":"forbidden"}), 403

@app.route('/api/movies')
def api_movies():
    cur = get_db().cursor()
    cur.execute("SELECT id, title FROM movies ORDER BY id LIMIT 50")
    rows = cur.fetchall()
    movies = [{"id": r[0], "title": r[1]} for r in rows]
    return jsonify(movies)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8000, debug=True)
