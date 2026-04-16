from flask import Flask, render_template, request, redirect, jsonify, session, Response
import sqlite3, datetime, os

app = Flask(__name__)
app.secret_key = "secret123"

DB_PATH = os.environ.get("DB_PATH", "/tmp/notes.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        last_updated TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# AUTH

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
            conn.commit()
        except:
            return "User exists"
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()
        if user:
            session['user_id'] = user['id']
            return redirect('/')
        return "Invalid login"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# NOTES

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    notes = conn.execute("SELECT * FROM notes WHERE user_id=?", (session['user_id'],)).fetchall()
    conn.close()

    return render_template('index.html', notes=notes)

@app.route('/create', methods=['POST'])
def create():
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (user_id,title,content,last_updated) VALUES (?,?,?,?)",
        (session['user_id'], "Untitled Note", "Start editing...", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/note/<int:note_id>')
def note(note_id):
    return render_template('note.html', note_id=note_id)

@app.route('/get_note/<int:note_id>')
def get_note(note_id):
    conn = get_db()
    note = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    conn.close()

    return jsonify({
        "content": note["content"],
        "title": note["title"],
        "last_updated": note["last_updated"]
    })

@app.route('/update_note/<int:note_id>', methods=['POST'])
def update_note(note_id):
    content = request.form['content']
    conn = get_db()
    conn.execute("UPDATE notes SET content=?,last_updated=? WHERE id=?",
                 (content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id))
    conn.commit()
    conn.close()
    return "OK"

@app.route('/rename/<int:note_id>', methods=['POST'])
def rename(note_id):
    title = request.form['title']
    conn = get_db()
    conn.execute("UPDATE notes SET title=? WHERE id=?", (title, note_id))
    conn.commit()
    conn.close()
    return "OK"

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete(note_id):
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
    return redirect('/')

# EXPORT

@app.route('/export/<int:note_id>')
def export(note_id):
    conn = get_db()
    note = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    conn.close()

    content = note["title"] + "\n\n" + note["content"]

    return Response(content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename=note_{note_id}.txt"})

# RUN

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)