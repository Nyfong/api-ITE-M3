from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Configure MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:typeslowly@database-1.cfc6seo846k2.us-east-1.rds.amazonaws.com:3306/expense_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Configure Swagger
app.config['SWAGGER'] = {
    'title': 'Expense Management API',
    'uiversion': 3,
    'description': 'API for managing users, categories, and expenses.'
}
swagger = Swagger(app)

# Import models (ensure models.py is in the same directory)
from model import User, Category, Expense

# User registration
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
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# Add category
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
    new_category = Category(name=data['name'], description=data.get('description'))
    db.session.add(new_category)
    db.session.commit()
    return jsonify({"message": "Category added successfully"}), 201

# Add expense
@app.route('/expenses', methods=['POST'])
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
            - user_id
            - category_id
            - amount
            - expense_type
            - expense_date
          properties:
            user_id:
              type: integer
              description: The ID of the user.
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
    new_expense = Expense(
        user_id=data['user_id'],
        category_id=data['category_id'],
        amount=data['amount'],
        expense_type=data['expense_type'],
        description=data.get('description'),
        expense_date=datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({"message": "Expense added successfully"}), 201

# Get all expenses
@app.route('/expenses', methods=['GET'])
def get_expenses():
    """
    Get all expenses.
    ---
    tags:
      - Expenses
    responses:
      200:
        description: A list of expenses.
        schema:
          type: array
          items:
            $ref: '#/definitions/Expense'
    """
    expenses = Expense.query.all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

# Swagger definition for Expense
@app.route('/swagger')
def swagger_spec():
    return jsonify(swagger.get_apispecs())

# Run the Flask app
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)