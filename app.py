from flask import Flask, request, jsonify, abort, session
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from sqlalchemy.exc import OperationalError

# Initialize Flask app
app = Flask(__name__)

# Configure MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:typeslowly@database-1.cfc6seo846k2.us-east-1.rds.amazonaws.com:3306/expense_management?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,  # Recycle connections after 1 hour
    'pool_timeout': 30,    # Timeout for acquiring a connection from the pool
    'max_overflow': 20,    # Maximum number of connections to create beyond the pool_size
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Configure Swagger
app.config['SWAGGER'] = {
    'title': 'Expense Management API',
    'uiversion': 3,
    'description': 'API for managing users, categories, and expenses.'
}
swagger = Swagger(app)

# Secret key for session management
app.secret_key = 'your-secret-key'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Define Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': str(self.created_at)
        }

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': str(self.created_at)
        }

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    expense_type = db.Column(db.Enum('Income', 'Expense'), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    expense_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'amount': self.amount,
            'expense_type': self.expense_type,
            'description': self.description,
            'expense_date': str(self.expense_date),
            'created_at': str(self.created_at)
        }

# Create database tables (run once)
with app.app_context():
    db.create_all()

# Helper function to validate date format
def validate_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        abort(400, description="Invalid date format. Use YYYY-MM-DD.")

# Login required decorator
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            abort(401, description="You must be logged in to access this resource.")
        return f(*args, **kwargs)
    return wrapper

# User Registration
@app.route('/users', methods=['POST'])
def register_user():
    """
    Register a new user.
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: UserRegistration
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              description: The user's username.
            email:
              type: string
              description: The user's email.
            password:
              type: string
              description: The user's password.
    responses:
      201:
        description: User registered successfully.
    """
    data = request.json
    if not data.get('username') or not data.get('email') or not data.get('password'):
        abort(400, description="Missing required fields: username, email, or password.")

    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except OperationalError as e:
        db.session.rollback()
        return jsonify({"error": "Database connection error. Please try again."}), 500

# User Login
@app.route('/login', methods=['POST'])
def login():
    """
    Log in a user.
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: UserLogin
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: The user's username.
            password:
              type: string
              description: The user's password.
    responses:
      200:
        description: User logged in successfully.
      401:
        description: Invalid username or password.
    """
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password_hash, data.get('password')):
        session['user_id'] = user.id
        return jsonify({"message": "User logged in successfully"}), 200
    else:
        abort(401, description="Invalid username or password.")

# User Logout
@app.route('/logout', methods=['POST'])
def logout():
    """
    Log out the current user.
    ---
    tags:
      - Users
    responses:
      200:
        description: User logged out successfully.
    """
    session.pop('user_id', None)
    return jsonify({"message": "User logged out successfully"}), 200

# Add Category
@app.route('/categories', methods=['POST'])
def add_category():
    """
    Add a new category.
    ---
    tags:
      - Categories
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: Category
          required:
            - name
          properties:
            name:
              type: string
              description: The name of the category.
            description:
              type: string
              description: A description of the category.
    responses:
      201:
        description: Category added successfully.
    """
    data = request.json
    if not data.get('name'):
        abort(400, description="Missing required field: name.")

    new_category = Category(name=data['name'], description=data.get('description'))
    
    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify({"message": "Category added successfully"}), 201
    except OperationalError as e:
        db.session.rollback()
        return jsonify({"error": "Database connection error. Please try again."}), 500

# Get all categories
@app.route('/categories', methods=['GET'])
def get_all_categories():
    """
    Get all categories.
    ---
    tags:
      - Categories
    responses:
      200:
        description: A list of all categories.
    """
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories]), 200

# Add Expense
@app.route('/expenses', methods=['POST'])
@login_required
def add_expense():
    """
    Add a new expense.
    ---
    tags:
      - Expenses
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: Expense
          required:
            - category_id
            - amount
            - expense_type
            - expense_date
          properties:
            category_id:
              type: integer
              description: The ID of the category.
            amount:
              type: number
              format: float
              description: The amount of the expense.
            expense_type:
              type: string
              enum: [Income, Expense]
              description: The type of the expense (Income or Expense).
            description:
              type: string
              description: A description of the expense.
            expense_date:
              type: string
              format: date
              description: The date of the expense (YYYY-MM-DD).
    responses:
      201:
        description: Expense added successfully.
    """
    data = request.json
    required_fields = ['category_id', 'amount', 'expense_type', 'expense_date']
    if not all(field in data for field in required_fields):
        abort(400, description=f"Missing required fields: {required_fields}")

    expense_date = validate_date(data['expense_date'])
    new_expense = Expense(
        user_id=session['user_id'],  # Use the logged-in user's ID
        category_id=data['category_id'],
        amount=data['amount'],
        expense_type=data['expense_type'],
        description=data.get('description'),
        expense_date=expense_date
    )
    
    try:
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({"message": "Expense added successfully"}), 201
    except OperationalError as e:
        db.session.rollback()
        return jsonify({"error": "Database connection error. Please try again."}), 500

# Get all expenses for the logged-in user
@app.route('/expenses', methods=['GET'])
@login_required
def get_all_expenses():
    """
    Get all expenses for the logged-in user.
    ---
    tags:
      - Expenses
    responses:
      200:
        description: A list of all expenses for the logged-in user.
    """
    expenses = Expense.query.filter_by(user_id=session['user_id']).all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

# Edit Expense
@app.route('/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def edit_expense(expense_id):
    """
    Edit an existing expense.
    ---
    tags:
      - Expenses
    parameters:
      - in: path
        name: expense_id
        required: true
        type: integer
        description: The ID of the expense to edit.
      - in: body
        name: body
        required: true
        schema:
          id: Expense
          properties:
            amount:
              type: number
              format: float
              description: The updated amount of the expense.
            expense_type:
              type: string
              enum: [Income, Expense]
              description: The updated type of the expense (Income or Expense).
            description:
              type: string
              description: The updated description of the expense.
            expense_date:
              type: string
              format: date
              description: The updated date of the expense (YYYY-MM-DD).
    responses:
      200:
        description: Expense updated successfully.
    """
    data = request.json
    expense = Expense.query.get_or_404(expense_id)

    # Ensure the expense belongs to the logged-in user
    if expense.user_id != session['user_id']:
        abort(403, description="You are not authorized to edit this expense.")

    if 'amount' in data:
        expense.amount = data['amount']
    if 'expense_type' in data:
        expense.expense_type = data['expense_type']
    if 'description' in data:
        expense.description = data['description']
    if 'expense_date' in data:
        expense.expense_date = validate_date(data['expense_date'])

    try:
        db.session.commit()
        return jsonify({"message": "Expense updated successfully"}), 200
    except OperationalError as e:
        db.session.rollback()
        return jsonify({"error": "Database connection error. Please try again."}), 500

# Delete Expense
@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    """
    Delete an expense.
    ---
    tags:
      - Expenses
    parameters:
      - in: path
        name: expense_id
        required: true
        type: integer
        description: The ID of the expense to delete.
    responses:
      200:
        description: Expense deleted successfully.
    """
    expense = Expense.query.get_or_404(expense_id)

    # Ensure the expense belongs to the logged-in user
    if expense.user_id != session['user_id']:
        abort(403, description="You are not authorized to delete this expense.")

    try:
        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully"}), 200
    except OperationalError as e:
        db.session.rollback()
        return jsonify({"error": "Database connection error. Please try again."}), 500

# Search Expenses by Date Range
@app.route('/expenses/date-range', methods=['GET'])
@login_required
def search_expenses_by_date_range():
    """
    Search for expenses by date range.
    ---
    tags:
      - Expenses
    parameters:
      - in: query
        name: start_date
        type: string
        format: date
        description: The start date for filtering expenses (YYYY-MM-DD).
      - in: query
        name: end_date
        type: string
        format: date
        description: The end date for filtering expenses (YYYY-MM-DD).
    responses:
      200:
        description: A list of expenses within the specified date range.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Expense.query.filter_by(user_id=session['user_id'])

    if start_date:
        query = query.filter(Expense.expense_date >= validate_date(start_date))
    if end_date:
        query = query.filter(Expense.expense_date <= validate_date(end_date))

    expenses = query.all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

# Search Expenses by Category
@app.route('/expenses/category/<int:category_id>', methods=['GET'])
@login_required
def search_expenses_by_category(category_id):
    """
    Search for expenses by category.
    ---
    tags:
      - Expenses
    parameters:
      - in: path
        name: category_id
        required: true
        type: integer
        description: The ID of the category.
    responses:
      200:
        description: A list of expenses for the specified category.
    """
    expenses = Expense.query.filter_by(user_id=session['user_id'], category_id=category_id).all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

# Run the Flask app
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)