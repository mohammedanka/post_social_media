from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_mysqldb import MySQL
from functools import wraps
import datetime

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'web'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#Log In Page 
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST' and request.form['username'] != '' and request.form['password'] != '':
		username = request.form['username']
		password = request.form['password']
		cur = mysql.connection.cursor()
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
		if result > 0:
			result_2 = cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", [username, password])
			user_data = cur.fetchall()
			if result_2 > 0:
				session['logged_in'] = True
				session['username'] = username
				for user_info in user_data:
					session['userId'] = user_info["userId"]
				return redirect(url_for('home'))
			else:
				error = 'Wrong password'
				return render_template('login.html', error = error)
		else:
			error = 'Username not found'
			return render_template('login.html', error = error)
	return render_template('login.html')

#Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		name = request.form['first']
		family = request.form['last']
		username = request.form['username']
		password = request.form['password']

		cur = mysql.connection.cursor()
		#Search if the username is avaiable
		result_1 = cur.execute("SELECT * FROM users WHERE username = %s", [username])
		if result_1 > 0:
			error = 'Username not avaiable'
			return render_template('register.html', error = error)
		else:
			#Insert the following data to main database
			cur.execute("INSERT INTO users(userId, firstName, lastName, username, password) VALUES( null, %s, %s, %s, %s)", (name, family, username, password))
			mysql.connection.commit()
			cur.close()
			flash('You are now registered and can log in', 'success')
			return redirect(url_for('login'))
	return render_template('register.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#Log Out and clear session
# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Home Page news Feed
@app.route('/home')
@is_logged_in
def home():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM posts ORDER BY date DESC")
    posts = cur.fetchall()
    if result > 0:
    	articles = []
    	for post in posts:
    		userId = post["userId"]
    		post_date = post["date"]
    		post_text = post["text"]
    		cur_2 = mysql.connection.cursor()
    		users = cur_2.execute("SELECT * FROM users WHERE userId = %s", [userId])
    		user_info = cur_2.fetchall()
    		for user in user_info:
    			name = user["firstName"]
    			family = user["lastName"]
    		username = name +" " + family
    		articles.append([ username, post_date, post_text])
    	return render_template('home.html', articles = articles, length = len(articles))
    else:
        msg = 'No posts Found'
        return render_template('home.html', msg=msg)
    cur.close()

#Insert a pos
@app.route('/add', methods=['GET', 'POST'])
@is_logged_in
def add():
	if request.method == 'POST':
		post_date = datetime.datetime.now()
		post_text = request.form['editor'];
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO posts VALUES(null, %s, %s, %s)",( session['userId'], post_date, post_text))
		mysql.connection.commit()
		cur.close()
		flash('Article Created', 'success')
		return render_template('add.html', msg = "Succes")
	return render_template('add.html')

# Go to my products page
@app.route('/myproducts')
@is_logged_in
def myproducts():
	cur = mysql.connection.cursor()
	posts = cur.execute("SELECT * FROM posts WHERE userId = %s", [session['userId']])
	articles = cur.fetchall()
	return render_template('myproducts.html', articles = articles, length = len(articles))

# Delete Post
@app.route('/delete/<int:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM posts WHERE postId = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('myproducts'))

# Edit Article
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def update(id):
    if request.method == 'POST':
        post_text = request.form['editor']
        post_date = datetime.datetime.now()
        userId = session['userId']
        cur = mysql.connection.cursor()
        cur.execute ("UPDATE posts SET text = %s, date = %s WHERE postId = %s AND userId = %s",(post_text, post_date, id, userId))
        mysql.connection.commit()
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('myproducts'))
    return render_template('edit.html')

if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)