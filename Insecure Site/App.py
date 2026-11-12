from flask import Flask, render_template, request, redirect, url_for, abort, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import werkzeug.exceptions
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField
from wtforms.validators import InputRequired, Length, DateRange
import json
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'very_secret'
auth = HTTPBasicAuth()

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
    birthDate DATE
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
     def __init__(self, id, username, password, admin=0):
          self.id = id
          self.username = username
          self.password = password
          self.admin = admin

class RegisterForm(FlaskForm):
    username = StringField("Username", validators = [InputRequired("Username required"), Length(min=5, max=25, message= "Username must be between 5 and 25 characters")])
    password = PasswordField("Password", validators=[InputRequired("Password required"), Length(min=10, max=128, message = "Password must be at least 10 characters and shorter than 128 characters")])
    birthDate = DateField("Birthdate", validators=[InputRequired("birthdate required"), DateRange(max=(2016,1,1), message = "You must be older to register")])
    submit = SubmitField("Register")

@loginManager.user_loader
def loadUser(id):
    with sqlite3.connect("database.db") as conn:
        user = conn.execute('SELECT * FROM USERS WHERE id = ?', (id,)).fetchone()
        if user:
             return User(user[0], user[1], user[2], user[3])
        return None

@auth.verify_password
def verify_password(username, password):
     with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
    
            cursor.execute("SELECT * FROM USERS WHERE username = ? LIMIT 1", (username,))
            userRow = cursor.fetchone()
    
            if not userRow is None and check_password_hash(userRow[2], password):
                return username

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


#error handlers
@app.errorhandler(werkzeug.exceptions.BadRequest)
def handleBadRequest(e):
    return "Bad request!", 400



@app.errorhandler(werkzeug.exceptions.Forbidden)
def handleBadRequest(e):
    return "You are fobidden from accessing this page", 403



@app.errorhandler(werkzeug.exceptions.NotFound)
def handleNotFound(e):
    return render_template("notFound.html"), 404

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
        try:
            with sqlite3.connect("database.db") as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM USERS WHERE username = ? LIMIT 1", (username,))
                userRow = cursor.fetchone()

                if userRow is None or not check_password_hash(userRow[2], password):
                    return render_template('login.html', error= "invalid username or password")

                user = User(userRow[0], userRow[1], userRow[2], userRow[3])
                login_user(user)

                return redirect("/content")
        except:
            print("Something went wrong in login")
    return render_template('login.html')

#register page
@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == "POST":
        if form.validate_on_submit:
            username = form.username.data
            password = form.password.data
            birthdate = form.birthDate.data


            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))

                if cursor.fetchone() is not None:
                    return render_template('register.html', error="Username already taken")
                cursor.execute("INSERT INTO USERS (username, password, admin, birthdate) VALUES (?,?,false,?)", (username, generate_password_hash(password), birthdate))
                conn.commit()

                return redirect("/login")
    return render_template('register.html', form=form)

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
    return render_template('content.html', admin = current_user.admin, username = current_user.username, data=data)




@app.route('/admin')
@admin_required
def admin():
    render_template('admin.html')
    


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if current_user.admin:
        with sqlite3.connect("database.db") as conn:
                    conn.execute('DELETE FROM POSTS WHERE id = ?', (id,))
                    conn.commit()
                    
    return redirect(url_for("content"))
                

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/retrieve', methods=['GET'])
@auth.login_required
def retrievePosts():
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        data = cursor.execute("SELECT * FROM POSTS").fetchall()
        conn.commit()
        return json.dumps( [dict(ix) for ix in data] )


if __name__ == '__main__':
    app.run(debug= False)