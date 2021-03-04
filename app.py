import os
import io
import base64

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, abort, Response
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from tempfile import mkdtemp
from helpers import login_required
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from random import randint

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finalproject.db")


@app.route("/")
@login_required
def index():
    """Show all of the qualities of the website(Main page)"""
    name = db.execute("SELECT username FROM users WHERE id=:id", id=session["user_id"]) #name of user queried from database using SQL
    time = datetime.now() # time is now containing date and time
    return render_template("index.html", username=name[0]["username"], current_time=time.strftime("%d/%m/%Y %H:%M:%S"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear() # Forget any previous user_id
    if request.method == "POST":

        if not request.form.get("username"):
            abort(403, 'Must Provide Username')

        elif not request.form.get("password"):
            abort(403, 'Must Provide Password')

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            abort(400, 'invalid username and/or password')

        session["user_id"] = rows[0]["id"]# Remember which user has logged in
        flash("Logged In")
        return redirect("/") # Redirect user to home page

    else:# User reached route via GET
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register the user"""
    if request.method == "POST":
        if not request.form.get("username"): #if username isn't provided
            return abort(403, "Must Input A Username")
        elif not request.form.get("password"):
            return abort(403, "Must Provide Password")
        elif not request.form.get("confirmation"): #if password comfirmation isn't provided
            return abort(403, "Must Provide Password Confirmation")
        elif not request.form.get("email"):
            return abort(403, "Must include an email address")
        elif request.form.get("password") != request.form.get("confirmation"): #password and confirmation must match
            return abort(403, "Passwords Must Match")

        #hash user's password
        hash = generate_password_hash(request.form.get("password"))
        user_name = request.form.get("username")
        #add user into database if they pass all restrictions
        U = db.execute("SELECT username FROM users WHERE username=:username", username=user_name)

        if len(U) != 0:
            return abort(409, "Username is already in use") #error code 409 for already in database

        data = db.execute("INSERT INTO users (username, hash, email) VALUES(:username, :hash, :email)", username=user_name, hash=hash, email=request.form.get("email"))

        session["user_id"] = data
        flash("Registered")
        # redirect the user
        return redirect("/")#later change to index.html
    else:
        return render_template("register.html")


@app.route("/links", methods=["GET"])
@login_required
def links():
    return render_template("links.html")


@app.route("/rate", methods=["GET", "POST"])
@login_required
def rate():
    """User Rates Website"""
    if request.method == "POST":
        if not request.form.get("star"):
            flash("Select a star rating")
        else:
            username = db.execute("SELECT username FROM users WHERE id=:id", id=session["user_id"])
            time = datetime.now() # time and date
            if not request.form.get("anonymous?"):
                db.execute("INSERT INTO rate (id, username, rating, comment, time) VALUES (:id, :username, :rating, :comment, :time)", id=session["user_id"], username=username[0]["username"], rating=request.form.get("star"), comment=request.form.get("comment"), time=time.strftime("%d/%m/%Y %H:%M:%S"))
            else:
                db.execute("INSERT INTO rate (id, username, rating, comment, time) VALUES (:id, :username, :rating, :comment, :time)", id=session["user_id"], username="ANONYMOUS USER", rating=request.form.get("star"), comment=request.form.get("comment"), time=time.strftime("%d/%m/%Y %H:%M:%S"))
        return redirect("/rate")
    else:
        #get the comments from datebase
        data = db.execute("SELECT * FROM rate")
        return render_template("rate.html", data=data, index=index)

@app.route("/week1", methods=["GET", "POST"])
@login_required
def wk1():
    if request.method == "POST":
        db.execute("DELETE FROM data WHERE id=:id", id=session["user_id"]) #delete EVERYTHING FROM data
        db.execute("DELETE FROM age WHERE id=:id", id=session["user_id"])
        db.execute("INSERT INTO data (id, day1, day2, day3, day4, day5, day6, day7) VALUES (:id, :day1, :day2, :day3, :day4, :day5, :day6, :day7)", id=session["user_id"], day1=request.form.get("day1"),
        day2=request.form.get("day2"), day3=request.form.get("day3"), day4=request.form.get("day4"), day5=request.form.get("day5"), day6=request.form.get("day6"), day7=request.form.get("day7"))

        db.execute("INSERT INTO datadump (id, day1, day2, day3, day4, day5, day6, day7) VALUES (:id, :day1, :day2, :day3, :day4, :day5, :day6, :day7)", id=session["user_id"], day1=request.form.get("day1"),
        day2=request.form.get("day2"), day3=request.form.get("day3"), day4=request.form.get("day4"), day5=request.form.get("day5"), day6=request.form.get("day6"), day7=request.form.get("day7"))
        return redirect("/week2")
    else:
        return render_template("week_1.html")


@app.route("/week2", methods=["GET", "POST"])
@login_required
def wk2():
    if request.method == "POST":
        db.execute("INSERT INTO data (id, day1, day2, day3, day4, day5, day6, day7) VALUES (:id, :day1, :day2, :day3, :day4, :day5, :day6, :day7)", id=session["user_id"], day1=request.form.get("day1"),
        day2=request.form.get("day2"), day3=request.form.get("day3"), day4=request.form.get("day4"), day5=request.form.get("day5"), day6=request.form.get("day6"), day7=request.form.get("day7"))

        db.execute("INSERT INTO datadump (id, day1, day2, day3, day4, day5, day6, day7) VALUES (:id, :day1, :day2, :day3, :day4, :day5, :day6, :day7)", id=session["user_id"], day1=request.form.get("day1"),
        day2=request.form.get("day2"), day3=request.form.get("day3"), day4=request.form.get("day4"), day5=request.form.get("day5"), day6=request.form.get("day6"), day7=request.form.get("day7"))
        return redirect("/week3")
    else:
        return render_template("week_2.html")


@app.route("/week3", methods=["GET", "POST"])
@login_required
def wk3():
    if request.method == "POST":
        db.execute("INSERT INTO data (id, day1, day2, day3, day4, day5, day6, day7) VALUES (:id, :day1, :day2, :day3, :day4, :day5, :day6, :day7)", id=session["user_id"], day1=request.form.get("day1"),
        day2=request.form.get("day2"), day3=request.form.get("day3"), day4=request.form.get("day4"), day5=request.form.get("day5"), day6=request.form.get("day6"), day7=request.form.get("day7"))

        db.execute("INSERT INTO datadump (id, day1, day2, day3, day4, day5, day6, day7) VALUES (:id, :day1, :day2, :day3, :day4, :day5, :day6, :day7)", id=session["user_id"], day1=request.form.get("day1"),
        day2=request.form.get("day2"), day3=request.form.get("day3"), day4=request.form.get("day4"), day5=request.form.get("day5"), day6=request.form.get("day6"), day7=request.form.get("day7"))

        db.execute("INSERT INTO age (id, age) VALUES (:id, :age)", id=session["user_id"], age=request.form.get("age"))
        return redirect("/quoted")
    else:
        return render_template("week_3.html")


@app.route("/quoted", methods=["GET"])
@login_required
def quoted():
    age = db.execute("SELECT * FROM age WHERE id=:id", id=session["user_id"])
    database = db.execute("SELECT day1, day2, day3, day4, day5, day6, day7 FROM data WHERE id=:id", id=session["user_id"])
    yplot= []
    for a in database:
        #print(a)
        for key in a.keys():
            #print(a[key])
            yplot.append(a[key])
    #print(yplot)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Graph of Sleep")
    axis.set_xlabel("DAYS")
    axis.set_ylabel("SLEEP HRS")
    axis.grid()
    #if age this later
    hline = [9 for i in range(0,21)]
    axis.plot(range(1,22), yplot , "r--", range(0,21), hline, "b--")
    # Convert plot to PNG image
    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage) #change the graph using this link; https://jakevdp.github.io/PythonDataScienceHandbook/04.01-simple-line-plots.html

    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    #------------------------------
    healthy_lvl=0
    healthy_lvl=[]
    if age[0]["age"] == "Birth to 3 months":
        for i in range(3):
            if 17 - int(database[i]["day1"]) <= 3 and 17 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 17 - int(database[i]["day2"]) <= 3 and 17 - int(database[i]["day2"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 17 - int(database[i]["day3"]) <= 3 and 17 - int(database[i]["day3"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 17 - int(database[i]["day4"]) <= 3 and 17 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 17 - int(database[i]["day5"]) <= 3 and 17 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 17 - int(database[i]["day6"]) <= 3 and 17 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 17 - int(database[i]["day7"]) <= 3 and 17 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")

        #healthy_lvl = 14 to 17 hours #if sleep minus 17 is less than equal to 3 and bigger than or equal to 0
    elif age[0]["age"] == "4 to 11 months":
        for i in range(3):
            if 16 - int(database[i]["day1"]) <= 4 and 16 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 16 - int(database[i]["day2"]) <= 4 and 16 - int(database[i]["day2"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 16 - int(database[i]["day3"]) <= 4 and 16 - int(database[i]["day3"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 16 - int(database[i]["day4"]) <= 4 and 16 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 16 - int(database[i]["day5"]) <= 4 and 16 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 16 - int(database[i]["day6"]) <= 4 and 16 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 16 - int(database[i]["day7"]) <= 4 and 16 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")

    #    healthy_lvl = 12 to 16 hours #if sleep minus 16 is less than equal to 4 and bigger than or equal to 0
    elif age[0]["age"] == "1 to 2 years":
        for i in range(3):
            if 14 - int(database[i]["day1"]) <= 3 and 14 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 14 - int(database[i]["day2"]) <= 3 and 14 - int(database[i]["day2"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 14 - int(database[i]["day3"]) <= 3 and 14 - int(database[i]["day3"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 14 - int(database[i]["day4"]) <= 3 and 14 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 14 - int(database[i]["day5"]) <= 3 and 14 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 14 - int(database[i]["day6"]) <= 3 and 14 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 14 - int(database[i]["day7"]) <= 3 and 14 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")

    #    healthy_lvl = 11 to 14 hours #if sleep minus 14 is less than equal to 3 and bigger than or equal to 0
    elif age[0]["age"] == "3 to 5 years":
        for i in range(3):
            if 13 - int(database[i]["day1"]) <= 3 and 13 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 13 - int(database[i]["day2"]) <= 3 and 13 - int(database[i]["day2"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 13 - int(database[i]["day3"]) <= 3 and 13 - int(database[i]["day3"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 13 - int(database[i]["day4"]) <= 3 and 13 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 13 - int(database[i]["day5"]) <= 3 and 13 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 13 - int(database[i]["day6"]) <= 3 and 13 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 13 - int(database[i]["day7"]) <= 3 and 13 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")

    #    healthy_lvl = 10 to 13 hours #if sleep minus 13 is less than equal to 3 and bigger than or equal to 0
    elif age[0]["age"] == "6 to 12 years":
        for i in range(3):
            if 12 - int(database[i]["day1"]) <= 3 and 12 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 12 - int(database[i]["day2"]) <= 3 and 12 - int(database[i]["day2"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 12 - int(database[i]["day3"]) <= 3 and 12 - int(database[i]["day3"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 12 - int(database[i]["day4"]) <= 3 and 12 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 12 - int(database[i]["day5"]) <= 3 and 12 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 12 - int(database[i]["day6"]) <= 3 and 12 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 12 - int(database[i]["day7"]) <= 3 and 12 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")

    #    healthy_lvl = 9 to 12 hours #if sleep minus 12 is less than equal to 3 and bigger than or equal to 0
    elif age[0]["age"] == "13 to 18 years":
        for i in range(3):
            if 10 - int(database[i]["day1"]) <= 2 and 10 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 10 - int(database[i]["day2"]) <= 2 and 10 - int(database[i]["day2"]) >= 0:
                    healthy_lvl.append("Healthy")
            else:
                    healthy_lvl.append("Unhealthy")
            if 10 - int(database[i]["day3"]) <= 2 and 10 - int(database[i]["day3"]) >= 0:
                    healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 10 - int(database[i]["day4"]) <= 2 and 10 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 10 - int(database[i]["day5"]) <= 2 and 10 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 10 - int(database[i]["day6"]) <= 2 and 10 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 10 - int(database[i]["day7"]) <= 2 and 10 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")

    #    healthy_lvl = 8 to 10 hours #if sleep minus 10 is less than equal to 2 and bigger than or equal to 0
    elif age[0]["age"] == "18 to 64 years":
        for i in range(3):
            if 9 - int(database[i]["day1"]) <= 2 and 9 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 9 - int(database[i]["day2"]) <= 2 and 9 - int(database[i]["day2"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 9 - int(database[i]["day3"]) <= 2 and 9 - int(database[i]["day3"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 9 - int(database[i]["day4"]) <= 2 and 9 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 9 - int(database[i]["day5"]) <= 2 and 9 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 9 - int(database[i]["day6"]) <= 2 and 9 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 9 - int(database[i]["day7"]) <= 2 and 9 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")

    #    healthy_lvl = 7 to 9 hours #if sleep minus 9 is less than equal to 2 and bigger than or equal to 0
    elif age[0]["age"] == "65 years and older":
        for i in range(3):
            if 8 - int(database[i]["day1"]) <= 1 and 8 - int(database[i]["day1"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 8 - int(database[i]["day2"]) <= 1 and 8 - int(database[i]["day2"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 8 - int(database[i]["day3"]) <= 1 and 8 - int(database[i]["day3"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 8 - int(database[i]["day4"]) <= 1 and 8 - int(database[i]["day4"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 8 - int(database[i]["day5"]) <= 1 and 8 - int(database[i]["day5"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 8 - int(database[i]["day6"]) <= 1 and 8 - int(database[i]["day6"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
            if 8 - int(database[i]["day7"]) <= 1 and 8 - int(database[i]["day7"]) >= 0:
                healthy_lvl.append("Healthy")
            else:
                healthy_lvl.append("Unhealthy")
    healthy = healthy_lvl.count("Healthy")
    unhealthy = healthy_lvl.count("Unhealthy")
    #    healthy_lvl = 7 to 8 hours #if sleep minus 8 is less than equal to 1 and bigger than or equal to 0
    return render_template("quoted.html", data=database, age=age[0]["age"], image=pngImageB64String, healthy_lvl=healthy_lvl, healthy=healthy, unhealthy=unhealthy)

@app.route("/compare", methods=["GET"])
@login_required
def compare():
    users = db.execute("SELECT id FROM datadump")
    list_users = []
    temp = 0
    for i in range(len(users)):
        if list_users.count(users[i]["id"]) == 0:
            list_users.append(users[i]["id"])
    list_users.sort()#sorts the list
    num_users = []
    while len(num_users) != 3: #pull three make sure to get unique
        temp = randint(1, max(list_users))
        if num_users.count(temp) == 0:
            num_users.append(temp)
    #where for the three id
    database1 = db.execute("SELECT day1, day2, day3, day4, day5, day6, day7 FROM datadump WHERE id=:id LIMIT 3", id=num_users[0])
    database2 = db.execute("SELECT day1, day2, day3, day4, day5, day6, day7 FROM datadump WHERE id=:id LIMIT 3", id=num_users[1])
    database3 = db.execute("SELECT day1, day2, day3, day4, day5, day6, day7 FROM datadump WHERE id=:id LIMIT 3", id=num_users[2])
    database_user = db.execute("SELECT day1, day2, day3, day4, day5, day6, day7 FROM data WHERE id=:id LIMIT 3", id=session["user_id"])
    yplot1 = []
    yplot2 = []
    yplot3 = []
    yplot4 = []

    for a in database1:
        for key in a.keys():
            yplot1.append(a[key])
    for a in database2:
        for key in a.keys():
            yplot2.append(a[key])
    for a in database3:
        for key in a.keys():
            yplot3.append(a[key])
    for a in database_user:
        for key in a.keys():
            yplot4.append(a[key])

    fig1 = Figure()
    axis = fig1.add_subplot(1, 1, 1)
    axis.set_title("PLOT")
    axis.set_xlabel("DAYS")
    axis.set_ylabel("SLEEP HRS")
    axis.grid()
    hline=[8 for i in range(1,22)]
    axis.plot(range(1,22), yplot1, "r--")
    axis.plot(range(1,22), hline, "y--")
    axis.plot(range(1,22), yplot2, "g--")
    axis.plot(range(1,22), yplot3, "b--")
    axis.plot(range(1,22), yplot4, "p-")

    pngImage = io.BytesIO()
    FigureCanvas(fig1).print_png(pngImage)

    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    return render_template("compare.html", image=pngImageB64String)


@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    """Settings where user can manipulate objects"""
    if request.method == "POST":
        #settings
        ALL = db.execute("SELECT hash FROM users WHERE id=:id", id=session["user_id"])
        if check_password_hash(ALL[0]["hash"], request.form.get("old_password")): #checking if the user inputted correct password
            # generate hash again for new password
            db.execute("UPDATE users SET hash=:hash WHERE id=:id", hash=generate_password_hash(request.form.get("new_password")), id=session["user_id"])
            flash("Password Change Successful")
        else:
            flash("Password Change Unsuccessful")
        return redirect("/settings")
    else:
        table_users = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])
        return render_template("settings.html", table_users=table_users, index=index)
