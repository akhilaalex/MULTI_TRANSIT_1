from flask import Flask, render_template, request, redirect, url_for, session , jsonify
import pyodbc
import re
from passlib.hash import pbkdf2_sha256
import secrets
from datetime import datetime, timedelta
import calendar


app = Flask(__name__)

# Replace this with your RDS connection details
rds_endpoint = 'your_rds_endpoint'
rds_database = 'your_database_name'
rds_username = 'your_username'
rds_password = 'your_password'

# Establishing a connection to RDS
conn_str = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={rds_endpoint};DATABASE={rds_database};UID={rds_username};PWD={rds_password}'
conn1 = pyodbc.connect(conn_str)
cursor1 = conn1.cursor()


#BUYING A NEW CARD

# Function to get the last date of the current month
def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return (next_month - timedelta(days=next_month.day)).date()



# Route for buying a new card
@app.route('/buy_card', methods=['GET', 'POST'])
def buy_card_():
    if request.method == 'POST':
        balance = float(request.form['balance'])
        monthly_pass = 'monthly_pass' in request.form
        expiry = last_day_of_month(datetime.now())

        # Use parameterized queries to prevent SQL injection
        cursor1.execute('''
            INSERT INTO TABLE_NAME (balance, monthly_pass, expiry)
            VALUES (?, ?, ?)
        ''', (balance, monthly_pass, expiry))

        conn1.commit()
        return redirect(url_for('buy_card_success'))

    return render_template('buy_card.html')

# Route for showing the success page after buying a new card
@app.route('/buy_card_success')
def buy_card_success():
    # Retrieve the latest card details from the database
    cursor1.execute('''
    SELECT  * FROM TABLE_NAME ORDER BY serial_no DESC
''')

    card_details = cursor1.fetchone()

    # Check if card details are available
    if card_details:
        serial_no = card_details.serial_no
        balance = card_details.balance
        monthly_pass = card_details.monthly_pass
        expiry = card_details.expiry

        return render_template('card_details.html',serial_no=serial_no, balance=balance,
                               monthly_pass=monthly_pass, expiry=expiry)
    else:
        return "Error retrieving card details."

if __name__ == '__main__':
    app.run(debug=True)