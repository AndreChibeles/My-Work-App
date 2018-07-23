from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps

app = Flask(__name__)
app.secret_key='secret123'

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'workappuser'
app.config['MYSQL_PASSWORD'] = 'pass'
app.config['MYSQL_DB'] = 'myworkapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)

#Index
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/<string:name>')
def index_login(name):
    return render_template('home.html', name=name)

####################################################
#            Registration Components               #
####################################################


# Registration Form Class
class RegisterFrom(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterFrom(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data

        if check_name(username):
            app.logger.info('%s exists', username)
            error = "User already exists"
            return render_template('registration/register.html', form=form, error=error)
        else:
            app.logger.info('User does not exist existe')

            #Create cursor
            cur = mysql.connection.cursor()

            #Execute the Query
            cur.execute("INSERT INTO users(name, email, username, password, users_date) VALUES(%s, %s, %s, %s, CURRENT_DATE())", (name, email, username, password))

            #Commit to DB
            mysql.connection.commit()

            #Close connection
            cur.close()

            flash('You are now registered and can log in', 'success')

            return redirect(url_for('index'))
    return render_template('registration/register.html', form=form)

def check_name(username):

    cur = mysql.connection.cursor()

    #Get user by username
    result = cur.execute("SELECT * FROM users WHERE username=%s", [username])
    app.logger.info('Entrei no checkname')
    if result>0:
        cur.close()
        return True
    else:
        cur.close()
        return False



#User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create cursor
        cur = mysql.connection.cursor()

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

        if result>0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare Passwords
            if password_candidate == password:
                app.logger.info('PASSWORD MATCHED')
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Loging'
                return render_template('login.html', error=error)
            #Close connection
            cur.close()
        else:
            error ='Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized', 'danger')
            return redirect(url_for('login'))
    return wrap



# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')



####################################################
#                   Final part                     #
####################################################


if __name__== '__main__':
    app.run(debug=True)    