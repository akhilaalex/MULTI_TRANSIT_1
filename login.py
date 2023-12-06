from flask import Flask, jsonify, request, session
import pyodbc
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


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()

        if not data or 'username_email' not in data or 'password' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid request data'})

        username_email = data['username_email']
        password = data['password']

        cursor.execute("SELECT * FROM TABLE_NAME WHERE user_email = ?", (username_email,))

        user = cursor.fetchone()

        if user and pbkdf2_sha256.verify(password, user.user_password):
            session['user_id'] = user.user_id
            return jsonify({'status': 'success', 'message': 'Login successful'})

        else:
            return jsonify({'status': 'error', 'message': 'Invalid login credentials'})

    return jsonify({'status': 'error', 'message': 'Invalid request method for this endpoint'})

@app.route('/welcome', methods=['POST'])
def welcome():
    if request.method == 'POST':
        data = request.get_json()

        if not data or 'action' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid request data'})

        action = data['action']

        if action == 'transit_select':
            selected_transit = data.get('transit_select')
            if selected_transit:
                return jsonify({'status': 'success', 'message': 'Redirecting', 'transit_name': selected_transit})

        elif action == 'logout':
            session.pop('user_id', None)
            return jsonify({'status': 'success', 'message': 'Logged out'})

    if 'user_id' in session:
        user_id = session['user_id']

        cursor.execute("SELECT first_name FROM TABLE_NAME WHERE user_id = ?", (user_id,))
        first_name = cursor.fetchone().first_name

        cursor.execute("SELECT transit_name FROM TABLE_NAME")
        transit_options = [row.transit_name for row in cursor.fetchall()]

        return jsonify({'status': 'success', 'first_name': first_name, 'transit_options': transit_options})
    else:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

@app.route('/logout', methods=['POST'])
def logout():
    if request.method == 'POST':
        session.pop('user_id', None)
        return jsonify({'status': 'success', 'message': 'Logged out'})

    return jsonify({'status': 'error', 'message': 'Invalid request'})

if __name__ == '__main__':
    app.run(debug=True)
