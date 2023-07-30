from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_migrate import Migrate
from datetime import datetime
import os

app = Flask(__name__)

# Use SQLite as the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hjpjhqolftannr:70f82a6b83db0db05c76deddcfd3a5c9ddae62c5725606e8d3f1624cf61659e3@ec2-52-5-167-89.compute-1.amazonaws.com:5432/ddmipft1gb65hv'

app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    is_signed_out = db.Column(db.Boolean, nullable=False, default=False)
    item_type = db.Column(db.String(80), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    signouts = db.relationship('Signout', backref='item', lazy=True)

class Technician(db.Model):
    __tablename__ = 'technicians'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    signouts = db.relationship('Signout', backref='technician', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Signout(db.Model):
    __tablename__ = 'signouts'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('technicians.id'))
    date_out = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_returned = db.Column(db.DateTime)
    returned = db.Column(db.Boolean, default=False)
    item_type = db.Column(db.String(80), nullable=False)

class ErrorLog(db.Model):
    __tablename__ = 'error_logs'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)

@app.errorhandler(Exception)
def handle_exception(e):
    error_msg = str(e)
    error_log = ErrorLog(message=error_msg)
    db.session.add(error_log)
    db.session.commit()
    return render_template('layout.html', error_msg=error_msg)

@app.route('/error')
def error_page():
    error_msg = request.args.get('error_msg')
    return render_template('error.html', error_msg=error_msg)

@app.route('/success')
def success():
    return render_template('success.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'tech_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    tech_id = session.get('tech_id')
    tech = Technician.query.get(tech_id)

    if tech is None:
        return redirect(url_for('error_page', error_msg='No tech found with the current tech_id'))

    items = Item.query.filter_by(is_signed_out=True).all()
    item_types = [item.item_type for item in items]

    signouts = Signout.query.all()  # Fetch all signouts without filtering by technician

    return render_template('home.html', tech=tech, item_types=item_types, signouts=signouts)


@app.route('/equipment', methods=['GET', 'POST'])
@login_required
def equipment():
    tech_id = session.get('tech_id')
    tech = Technician.query.get(tech_id)

    if tech is None:
        return redirect(url_for('error_page', error_msg='No tech found with the current tech_id'))

    if request.method == 'POST':
        item_id = request.form.get('item_id')

        if item_id is not None:
            item = Item.query.get(item_id)
            if item is None or item.is_signed_out:
                return redirect(url_for('error_page', error_msg='Invalid or already signed out item.'))
            else:
                item.is_signed_out = True
                item_type = item.item_type

        # Check that at least one item is signed out
        if item_id is None:
            return redirect(url_for('error_page', error_msg='You must sign out an item.'))

        signout = Signout(
            technician_id=tech_id,
            item_id=item_id,
            date_out=datetime.now(),
            item_type=item_type
        )
        db.session.add(signout)

        try:
            db.session.commit()
            flash('Item signed out successfully', 'success')
            return redirect(url_for('equipment'))
        except exc.IntegrityError:
            db.session.rollback()
            return redirect(url_for('error_page', error_msg='There was an error processing your request.'))

    items = Item.query.filter_by(is_signed_out=False).all()
    tech_signouts = Signout.query.filter_by(technician_id=tech_id, returned=False).all()

    return render_template('equipment.html', tech=tech, items=items, tech_signouts=tech_signouts)


@app.route('/get_equipment', methods=['GET'])
@login_required
def get_equipment():
    items = Item.query.filter_by(is_signed_out=False).all()
    equipment = [{'id': item.id, 'name': item.name, 'type': item.item_type} for item in items]
    return jsonify(equipment)

@app.route('/add_group', methods=['GET', 'POST'])
@login_required
def add_group():
    if request.method == 'POST':
        name = request.form.get('name')
        if Group.query.filter_by(name=name).first():
            return redirect(url_for('error_page', error_msg='The group already exists.'))
        new_group = Group(name=name)
        db.session.add(new_group)
        try:
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            return redirect(url_for('error_page', error_msg='The group already exists.'))
        return redirect(url_for('add_group'))
    return render_template('add_group.html')

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def items():
    if request.method == 'POST':
        name = request.form.get('name')
        item_type = request.form.get('type')
        group_id = request.form.get('group_id')

        if None in [name, item_type, group_id]:
            return redirect(url_for('error_page', error_msg='All fields are required.'))

        item = Item(name=name, item_type=item_type, group_id=group_id)
        db.session.add(item)

        try:
            db.session.commit()
            flash('Item added successfully', 'success')
            return redirect(url_for('items'))
        except exc.IntegrityError:
            db.session.rollback()
            return redirect(url_for('error_page', error_msg='An error occurred. Please try again.'))

    groups = Group.query.all()
    return render_template('add_item.html', groups=groups)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        tech = Technician.query.filter_by(name=name).first()
        if tech and tech.check_password(password):
            session['tech_id'] = tech.id
            return redirect(url_for('home'))
        else:
            return redirect(url_for('error_page', error_msg='Invalid username or password'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('tech_id', None)
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        if Technician.query.filter_by(name=name).first():
            return redirect(url_for('error_page', error_msg='A technician with that name already exists. Please use a different name.'))
        tech = Technician(name=name)
        tech.set_password(password)
        db.session.add(tech)
        try:
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            return redirect(url_for('error_page', error_msg='A technician with that name already exists. Please use a different name.'))
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/return_item', methods=['POST'])
@login_required
def return_item():
    tech_id = session.get('tech_id')
    signout_id = request.form.get('signout_id')
    signout = Signout.query.get(signout_id)

    if not signout or signout.technician_id != tech_id:
        return redirect(url_for('error_page', error_msg="Invalid signout ID or you cannot return an item you didn't sign out."))

    if signout.returned:
        return redirect(url_for('error_page', error_msg="This item has already been returned."))

    try:
        if signout.item_id is not None:
            item = Item.query.get(signout.item_id)
            if item:
                item.is_signed_out = False

        signout.returned = True
        signout.date_returned = datetime.now()

        db.session.commit()
        flash('Item returned successfully', 'success')
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('error_page', error_msg=f"An error occurred while returning the item: {str(e)}"))

    return redirect(url_for('equipment'))

@app.route('/testing')
@login_required #this actually handles the < -- signing out processes  -- > 
def ui():
    return render_template('testing.html')


@app.route('/layout')
@login_required
def layout():
    return render_template('layout.html')   


if __name__ == '__main__':
    with app.app_context():
        migrate.init_app(app, db)
        db.create_all()
        app.run(debug=True)
