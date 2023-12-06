from flask import Flask, jsonify, request
import pyodbc
import re
from passlib.hash import pbkdf2_sha256
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Replace this with your RDS connection details
rds_endpoint = 'your_rds_endpoint'
rds_database = 'your_database_name'
rds_username = 'your_username'
rds_password = 'your_password'

# Establishing a connection to RDS
conn_str = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={rds_endpoint};DATABASE={rds_database};UID={rds_username};PWD={rds_password}'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

def is_valid_name(name):
    return len(name) >= 2 and name.isalpha()

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def format_phone(phone):
    return f'+1 ({phone[:3]}) {phone[3:6]}-{phone[6:]}'

def is_valid_phone(phone):
    pattern = r'^\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'
    return re.match(pattern, phone) is not None

def is_email_unique(email):
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_email = ?", (email,))
    count = cursor.fetchone()[0]
    return count == 0

def is_strong_password(password):
    return (
        len(password) >= 8 and
        any(char.isupper() for char in password) and
        any(char.islower() for char in password) and
        any(char.isdigit() for char in password) and
        any(char in '!@#$%^&*()-_=+[]{}|;:\'",.<>/?' for char in password)
    )

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Passwords do not match. Please try again."

        if not is_valid_name(first_name) or not is_valid_name(last_name):
            return "Invalid first name or last name format. Please check and try again."

        if not is_valid_email(email):
            return "Invalid email format. Please enter a valid email address."

        if not is_valid_phone(phone_number):
            return "Invalid phone number format. Please enter a valid Canadian phone number."

        formatted_phone = format_phone(phone_number)

        if not is_email_unique(email):
            return "Email already exists. Please use a different email address."

        if not is_strong_password(password):
            return "Password does not meet the strong password policy. Please try again."

        hashed_password = pbkdf2_sha256.hash(password)

        cursor.execute('''
            INSERT INTO TABLE_NAME ( user_password, user_email, user_phn_no, first_name, last_name)
            VALUES ( ?, ?, ?, ?, ?)
        ''', (hashed_password, email, formatted_phone, first_name, last_name))

        conn.commit()
        return jsonify({'status': 'success', 'message': 'Registration successful!'})

    return jsonify({'status': 'error', 'message': 'Invalid request method for this endpoint'})

@app.route('/registration_success')
def registration_success():
    return "Registration successful!"

if __name__ == '__main__':
    app.run(debug=True)
