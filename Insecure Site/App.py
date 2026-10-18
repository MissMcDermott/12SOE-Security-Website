from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'very_secret'



#creating the database tables if they are not already there
connect = sqlite3.connect('database.db')
connect.execute('''
    CREATE TABLE IF NOT EXISTS USERS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    admin BINARY NOT NULL,
    birthDate DATE,
    cardNum TEXT,
    expiry DATE,
    cvc INTEGER,
    maiden TEXT,
    mbti TEXT
    )
    ''')

connect.execute('''
    CREATE TABLE IF NOT EXISTS POSTS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL
    )
    ''')

#connect.execute(''' DROP TABLE USERS''')


#home page
@app.route('/')
def index():
    return render_template('index.html')

#login page
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM USERS WHERE username = ? LIMIT 1", (username,))
            userRow = cursor.fetchone()

            if userRow is None:
                return render_template('login.html', error= "invalid username")

            if userRow[2] != password:
                return render_template('login.html', error= "incorrect password")


            return redirect("/content")
            
    return render_template('login.html')

#register page
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        birthdate = request.form.get("birthdate")
        cardNum = request.form.get("cardNum")
        expiry = request.form.get("expiry")
        cvc = request.form.get("cvc")
        maiden = request.form.get("maiden")
        mbti = request.form.get("mbti")

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))

            if cursor.fetchone() is not None:
                return render_template('register.html', error="Username already taken")
            cursor.execute("INSERT INTO USERS (username, password, admin, birthdate, cardNum, expiry, cvc, maiden, mbti) VALUES (?,?,false,?,?,?,?,?,?)", (username, password, birthdate, cardNum, expiry, cvc, maiden, mbti))
            conn.commit()

            return redirect("/login")
    return render_template('register.html')

#content page
@app.route('/content', methods = ['GET', 'POST'])
def content():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        with sqlite3.connect("database.db") as post:
            cursor = post.cursor()
            cursor.execute("INSERT INTO POSTS (title,content) VALUES (?,?)", (title, content))
            post.commit()

    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM POSTS')

    data = cursor.fetchall()
    print(data)
    connect.close()
    return render_template('content.html', data=data)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
     with sqlite3.connect("database.db") as conn:
                 conn.execute('DELETE FROM POSTS WHERE id = ?', (id,))
                 conn.commit()
                 return redirect(url_for("content"))
                
if __name__ == '__main__':
    app.run(debug= False)