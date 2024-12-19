from flask import Flask, request, jsonify
from model import db, User, Category, Expense
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Configure MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:typeslowly@database-1.cfc6seo846k2.us-east-1.rds.amazonaws.com:3306/expense_management'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# User registration
@app.route('/users', methods=['POST'])
def register_user():
    data = request.json
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# Add category
@app.route('/categories', methods=['POST'])
def add_category():
    data = request.json
    new_category = Category(name=data['name'], description=data.get('description'))
    db.session.add(new_category)
    db.session.commit()
    return jsonify({"message": "Category added successfully"}), 201

# Add expense
@app.route('/expenses', methods=['POST'])
def add_expense():
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
    expenses = Expense.query.all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

# Edit expense
@app.route('/expenses/<int:id>', methods=['PUT'])
def edit_expense(id):
    data = request.json
    expense = Expense.query.get(id)
    if not expense:
        return jsonify({"message": "Expense not found"}), 404

    expense.category_id = data['category_id']
    expense.amount = data['amount']
    expense.expense_type = data['expense_type']
    expense.description = data.get('description')
    expense.expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({"message": "Expense updated successfully"}), 200

# Delete expense
@app.route('/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    expense = Expense.query.get(id)
    if not expense:
        return jsonify({"message": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted successfully"}), 200

# Search expenses by date range
#/expenses/search?start_date=2023-01-01&end_date=2023-12-31
@app.route('/expenses/search', methods=['GET'])
def search_expenses():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    expenses = Expense.query.filter(
        Expense.expense_date >= datetime.strptime(start_date, '%Y-%m-%d').date(),
        Expense.expense_date <= datetime.strptime(end_date, '%Y-%m-%d').date()
    ).all()
    return jsonify([expense.to_dict() for expense in expenses]), 200


@app.route('/expenses/search_category', methods=['GET'])
def search_expenses_by_category():
    # Get category_name from request parameter
    category_name = request.args.get('category_name')

    if not category_name:
        return jsonify({"message": "Category name is required!"}), 400

    # Query the Expense table, joining with the Category table, and filtering by category name
    expenses = Expense.query.join(Category, Category.id == Expense.category_id).filter(Category.name == category_name).all()

    # If no expenses are found, return a message
    if not expenses:
        return jsonify({"message": f"No expenses found for category '{category_name}'"}), 404

    # Return the expenses as JSON
    return jsonify([expense.to_dict() for expense in expenses]), 200


# Run the Flask app
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)