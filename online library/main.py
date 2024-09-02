from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL


app = Flask(__name__)
app.secret_key = "library"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'library'

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == "POST":
        id = request.form['id']
        name = request.form['name']
        course = request.form['course']
        year = request.form['year']
        email = request.form['email']
        password = request.form['password']
        repassword = request.form['repassword']

        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE Id = %s', (id,))
        id_count = cursor.fetchone()[0]

        if id_count > 0:
            flash('⚠️ This ID is already in use.')
            return redirect(url_for('signin'))

        
        cursor.execute('SELECT COUNT(*) FROM users WHERE Email = %s', (email,))
        email_count = cursor.fetchone()[0]
        
        cursor.close()

        if email_count > 0 and password != repassword:
            flash('⚠️ Email is already in use and Passwords do not match')
            return redirect(url_for('signin'))
        elif email_count > 0:
            flash('⚠️ Email is already in use.')
            return redirect(url_for('signin'))
        elif password != repassword:
            flash('⚠️ Passwords do not match.')
            return redirect(url_for('signin'))

        # insert data sa user table
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (Id, Name, Course, Year, Email, Password) VALUES (%s, %s, %s, %s, %s, %s)',
                       (id, name, course, year, email, password))

        mysql.connection.commit()
        cursor.close()

    
        session['id'] = id
        return redirect(url_for('login'))

    return render_template('signin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT Id FROM users WHERE Email = %s AND Password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['id'] = user[0]
            return redirect(url_for('home'))
        
        elif email == "admin@phinmaed.com" and password == "admin":
            return redirect(url_for("admin_index"))
        else:
            flash('Wrong account number or password')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    user_id = session.get('id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT Name FROM users WHERE Id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        bdate = request.form["bdate"]
        rdate = request.form["rdate"]

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO books (Title, Author, Borrow_Date, Return_Date, Id) VALUES (%s, %s, %s, %s, %s)',
                       (title, author, bdate, rdate, user_id))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('borrow'))

    return render_template('home.html', user=user)

@app.route('/borrow')
def borrow():
    user_id = session.get('id')
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT Title, Author, Borrow_Date, Return_Date 
        FROM books 
        WHERE Id = %s 
        ORDER BY Borrow_Date DESC 
        LIMIT 1
    """, (user_id,))
    
    books = cursor.fetchone()
    cursor.close()

    return render_template("borrow.html", books=books)



@app.route('/notifications')
def notifications():
   
    
    return render_template('notifications.html')

@app.route('/profile')
def profile():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE Id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        user_data = {
            'id': user[0],
            'name': user[1],
            'course': user[2],
            'year': user[3],
            'email': user[4]
        }
        return render_template('profile.html', user=user_data)
    else:
        flash('User not found.')
        return redirect(url_for('login'))
   
    

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    user_id = session.get('id')
    
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    
    # Fetch current profile data
    cursor.execute("SELECT Id, Name, Course, Year, Email FROM users WHERE Id = %s", (user_id,))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        new_id = request.form['id']
        name = request.form['name']
        course = request.form['course']
        year = request.form['year']
        email = request.form['email']
        
        
        cursor.execute("""
            UPDATE users 
            SET Id = %s, Name = %s, Course = %s, Year = %s, Email = %s 
            WHERE Id = %s
        """, (new_id, name, course, year, email, user_id))
        
        mysql.connection.commit()
        cursor.close()
        
        
        session['id'] = new_id
        
        flash('Profile updated successfully.')
        return redirect(url_for('profile'))
    
    cursor.close() 
    return render_template('update_profile.html', user=user)



@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('index')) 

if __name__ == "__main__":
    app.run(debug=True)
