from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import datetime

app = Flask(__name__)

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("notes.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            last_updated TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------

@app.route('/')
def index():
    conn = get_db()
    notes = conn.execute("SELECT * FROM notes").fetchall()
    conn.close()
    return render_template("index.html", notes=notes)

@app.route('/create', methods=['POST'])
def create():
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (title, content, last_updated) VALUES (?, ?, ?)",
        ("Untitled Note", "Start editing...", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/note/<int:note_id>')
def note(note_id):
    return render_template("note.html", note_id=note_id)

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
    conn.execute(
        "UPDATE notes SET content=?, last_updated=? WHERE id=?",
        (content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id)
    )
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

# ---------- RUN ----------
import os

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))