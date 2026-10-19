from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'very_secret'

loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'

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

class User(UserMixin):
     def __init__(self, id, username, password):
          self.id = id
          self.username = username
          self.password = password

@loginManager.user_loader
def loadUser(id):
    with sqlite3.connect("database.db") as conn:
        user = conn.execute('SELECT * FROM USERS WHERE id = ?', (id,)).fetchone()
        if user:
             return User(user[0], user[1], user[2])
        return None

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


            user = User(userRow[0], userRow[1], userRow[2])
            login_user(user)

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
@login_required
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
    return render_template('content.html', username = current_user.username, data=data)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
     with sqlite3.connect("database.db") as conn:
                 conn.execute('DELETE FROM POSTS WHERE id = ?', (id,))
                 conn.commit()
                 return redirect(url_for("content"))
                

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug= False)