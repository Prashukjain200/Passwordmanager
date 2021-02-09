from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email
import email_validator
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, logout_user
import datetime
import random

today = datetime.datetime.now()
req_date = today.strftime("%B,%d %Y")

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

#Authentication
app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = '49itk5krtgktpr5ktgprkyh'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passwordsq.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

#Making Database
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False, unique=False)
    users = db.relationship('Passwordsq', backref='owner')


class Passwordsq(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    website = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
db.create_all()


#Using WTF Flask Forms
class FirstForm(FlaskForm):
    website = StringField("Website name", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    name = StringField("Your Name", validators=[DataRequired()])
    submit = SubmitField("Submit")

class SecondForm(FlaskForm):
    alphabet = StringField("Number of Alphabet", validators=[DataRequired()])
    number = StringField("Number of Digits", validators=[DataRequired()])
    symbol = StringField("Number of Symbols", validators=[DataRequired()])
    submit = SubmitField("Generate")

class LoginForm(FlaskForm):
    email = StringField("Write your Email", validators=[DataRequired(), Email()])
    password = PasswordField("Write your Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

#Register Part
@app.route("/register", methods=["GET", "POST"])
def register():
    form = LoginForm()
    if form.validate_on_submit():
        hash_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            flash('You are already registered')
            return redirect(url_for('login'))
        new_user = User(
            email=email,
            password=hash_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Successfully Registered')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#Lgin Part
@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with this username. Try to register first")
            return redirect(url_for('register'))
        if check_password_hash(user.password, password):
            req_id = user.id
            return redirect(url_for('home', req_id=req_id))
        else:
            flash("Password Incorrent. Please check your Password")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)

#Home Page after Login
@app.route("/home")
def home():
    req = request.args.get("req")
    req_id = request.args.get("req_id")
    data = Passwordsq.query.filter_by(owner_id=req_id)
    date = req_date
    return render_template("index.html", data=data, date=date, req_id=req_id, req=req)

#Automatic Password generator
@app.route("/generate")
def generate():
    req_id = request.args.get("req_id")
    final = []
    for _ in range(4):
        first = random.choice(letters)
        final.append(first)
    for _ in range(3):
        second = random.choice(numbers)
        final.append(second)
    for _ in range(2):
        third = random.choice(symbols)
        final.append(third)
    random.shuffle(final)
    space = ""
    req = space.join(final)
    return render_template("generated.html", req=req, req_id=req_id)

#Logout Part
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

#Add Credentials
@app.route("/add", methods=["GET", "POST"])
def add():
    req = request.args.get('req')
    req_id = request.args.get("req_id")
    print(req_id)
    req_user = User.query.get(req_id)
    form = FirstForm(
        password=req
    )
    if form.validate_on_submit():
        website = form.website.data
        password = form.password.data
        name = form.name.data
        req_data = Passwordsq(website=website, password=password, date=name, owner=req_user)
        db.session.add(req_data)
        db.session.commit()
        return redirect(url_for("home", req_id=req_id))
    return render_template("add.html", form=form)

#Edit Uploaded Data
@app.route("/edit<int:index>", methods=["GET", "POST"])
def edit(index):
    req_id = request.args.get("req_id")
    req_data = db.session.query(Passwordsq).get(index)
    form = FirstForm(
        website=req_data.website,
        password=req_data.password,
        name=req_data.date
    )
    if form.validate_on_submit():
        req_data.website=form.website.data
        req_data.password=form.password.data
        req_data.date=form.name.data
        db.session.commit()
        return redirect(url_for("home", req_id=req_id))
    return render_template("edit.html", form=form, req_id=req_id)

#Generating Manual Passowrd
@app.route("/manual", methods=["GET", "POST"])
def manual():
    req_id = request.args.get("req_id")
    form = SecondForm()
    if form.validate_on_submit():
        L = int(form.alphabet.data)
        N = int(form.number.data)
        S = int(form.symbol.data)
        final = []
        for _ in range(L):
            first = random.choice(letters)
            final.append(first)
        for _ in range(N):
            second = random.choice(numbers)
            final.append(second)
        for _ in range(S):
            third = random.choice(symbols)
            final.append(third)
        random.shuffle(final)
        space = ""
        req = space.join(final)
        return render_template("manually.html", req=req, req_id=req_id)
    return render_template("manual.html", form=form)

#About over team
@app.route("/about")
def about():
    req_id = request.args.get("req_id")
    return render_template("about.html", req_id=req_id)

#delete registered data
@app.route("/delete")
def delete():
    cred_id = request.args.get("cred_id")
    req_id = request.args.get("req_id")
    req = Passwordsq.query.get(cred_id)
    db.session.delete(req)
    db.session.commit()
    return redirect(url_for("home", req_id=req_id ))


if __name__ == "__main__":
    app.run()
