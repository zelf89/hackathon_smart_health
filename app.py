from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import psycopg2
from dotenv import load_dotenv
import os
import google.generativeai as genai
from datetime import datetime

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# Access the variables using os.environ or os.getenv()
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

app.secret_key = app.config['SECRET_KEY']  # Needed for session management


# PostgreSQL connection
try:
    conn = psycopg2.connect(
        host="localhost",
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USERNAME"),
        password=os.getenv("DATABASE_PASSWORD")
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    
    print("✅ Connected to PostgreSQL:", db_version[0])
    

except Exception as e:
    print("❌ Connection failed:", e)


# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_KEY"))

# # Start a chat session with a system-like prompt
# system_prompt = "You are an appointment booking assistant. Your task is to ask the user for location, date, and time when they want to book an appointment. Be polite and guide them step by step."

# # Initialize history with the system prompt
# history = [{"role": "system", "content": system_prompt}]

# Create the model and start a chat session
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

# Function to book an appointment
def book_appointment(user, location, date, time):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO appointments (username, appointment_location, appointment_date, appointment_time)
            VALUES (%s, %s, %s, %s);
        """, (user, location, date, time))
        conn.commit()
        cur.close()
        flash('Your appointment has been booked successfully!')
    except Exception as e:
        flash(f'An error occurred while booking your appointment: {e}')

def get_user_appointments(username):
    try:
        # Query the database to get appointments for the current user
        cur.execute("""
            SELECT appointment_location, appointment_date, appointment_time 
            FROM appointments 
            WHERE username = %s
            ORDER BY appointment_date DESC
        """, (username,))
        appointments = cur.fetchall()
        
        # Format the appointments as a list of strings
        if appointments:
            formatted_appointments = "\n".join([f"Location: {a[0]}, Date: {a[1]}, Time: {a[2]}" for a in appointments])
        else:
            formatted_appointments = "You have no upcoming appointments."

        return formatted_appointments

    except Exception as e:
        return f"Error fetching appointments: {str(e)}"

# @app.route('/', methods=['GET', 'POST'])
# def login():
#     if 'user' in session:
#         return redirect(url_for('main'))

#     if request.method == 'POST':
#         user_id = request.form['userId']
#         password = request.form['password']
#         login_type = request.form['loginType']

#         cur = conn.cursor()
#         result = None

#         if login_type == 'patient':
#             patient_id_type = request.form['patientIdType']
#             if patient_id_type == 'bruhims':
#                 cur.execute("SELECT bruhims, password FROM users WHERE bruhims=%s AND password=%s", (user_id, password))
#             else:
#                 cur.execute("SELECT ic, password FROM users WHERE ic=%s AND password=%s", (user_id, password))
#             result = cur.fetchone()

#         elif login_type == 'doctor':
#             cur.execute("SELECT id, name, password FROM doctor WHERE id=%s AND password=%s", (user_id, password))
#             result = cur.fetchone()

#         cur.close()

#         if result:
#             session['user'] = result[0]
#             session['name'] = result[1]
#             session['type'] = login_type
#             # return redirect(url_for('main'))
#               # Redirect based on type
#             if login_type == 'patient':
#                 return redirect(url_for('main'))
#             else:
#                 return redirect(url_for('doctor_dashboard'))
#         else:
#             flash('Invalid credentials. Please try again.')
            

#     return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('main'))

    login_type = 'patient'  # Default to 'patient' if not set

    if request.method == 'POST':
        user_id = request.form['userId']
        password = request.form['password']
        login_type = request.form['loginType']

        cur = conn.cursor()
        result = None

        if login_type == 'patient':
            patient_id_type = request.form['patientIdType']
            if patient_id_type == 'bruhims':
                cur.execute("SELECT bruhims, password FROM users WHERE bruhims=%s AND password=%s", (user_id, password))
            else:
                cur.execute("SELECT ic, password FROM users WHERE ic=%s AND password=%s", (user_id, password))
            result = cur.fetchone()

        elif login_type == 'doctor':
            cur.execute("SELECT id, name, password FROM doctor WHERE id=%s AND password=%s", (user_id, password))
            result = cur.fetchone()

        cur.close()

        if result:
            session['user'] = result[0]
            session['name'] = result[1]
            session['type'] = login_type
            # Redirect based on type
            if login_type == 'patient':
                return redirect(url_for('main'))
            else:
                return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid credentials. Please try again.')
            # Stay on the login page if login fails, passing the login_type to render the correct form
            return render_template('login.html', login_type=login_type)

    return render_template('login.html', login_type=login_type)

# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor_dashboard():
#     if 'user' not in session or session.get('type') != 'doctor':
#         flash("Please log in as a doctor to access this page.")
#         return redirect(url_for('login'))

#     doctor_id = session['user']
#     cur = conn.cursor()

#     # Handle approval action (approve/reject)
#     if request.method == 'POST':
#         appointment_id = request.form.get('appointment_id')
#         action = request.form.get('action')  # 'approve' or 'reject'
        
#         if action == 'approve':
#             # Update appointment to 'approved'
#             cur.execute("UPDATE appointment SET status='Approved' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))
#         elif action == 'reject':
#             # Update appointment to 'rejected'
#             cur.execute("UPDATE appointment SET status='Rejected' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))

#         elif action == 'pending':
#             # Update appointment to 'pending'
#             cur.execute("UPDATE appointment SET status='Pending' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))

#         elif action == 'complete':
#             # Update appointment to 'complete'
#             cur.execute("UPDATE appointment SET status='Completed' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))
        
#         conn.commit()

#     # Fetch appointments for this doctor
#     cur.execute("""
#         SELECT a.id, u.username, u.bruhims, u.ic, a.date, a.time, a.status
#         FROM appointment a
#         JOIN users u ON a.user_id = u.id
#         WHERE a.doctor_id = %s
#         ORDER BY a.date ASC, a.time ASC
#     """, (doctor_id,))
#     appointments = cur.fetchall()
#     cur.close()

#     return render_template('doctor.html', appointments=appointments)

@app.route('/doctor', methods=['GET', 'POST'])
def doctor_dashboard():
    if 'user' not in session or session.get('type') != 'doctor':
        flash("Please log in as a doctor to access this page.")
        return redirect(url_for('login'))

    doctor_id = session['user']
    cur = conn.cursor()

    medications = None  # default to None so template can check

    # If POST, it can be either appointment action OR search
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        action = request.form.get('action')  
        search_query = request.form.get('search_query')

        if appointment_id and action:
            # Handle appointment updates
            if action == 'approve':
                cur.execute("UPDATE appointment SET status='Approved' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))
            elif action == 'reject':
                cur.execute("UPDATE appointment SET status='Rejected' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))
            elif action == 'pending':
                cur.execute("UPDATE appointment SET status='Pending' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))
            elif action == 'complete':
                cur.execute("UPDATE appointment SET status='Completed' WHERE id=%s AND doctor_id=%s", (appointment_id, doctor_id))

            conn.commit()

        elif search_query:
            # Handle medication search
            cur.execute("""
                 SELECT u.username, u.bruhims, u.ic, m.medicine_name, m.typical_dose, m.times_per_day, m.reminder_times
                    FROM user_medications m
                    JOIN users u ON m.user_id = u.id
                    WHERE u.bruhims = %s OR u.ic = %s
            """, (search_query, search_query))
            medications = cur.fetchall()

    # Fetch appointments for this doctor
    cur.execute("""
        SELECT a.id, u.username, u.bruhims, u.ic, a.date, a.time, a.status
        FROM appointment a
        JOIN users u ON a.user_id = u.id
        WHERE a.doctor_id = %s
        ORDER BY a.date ASC, a.time ASC
    """, (doctor_id,))
    appointments = cur.fetchall()
    cur.close()

    return render_template('doctor.html', appointments=appointments, medications=medications)

@app.route('/main')
def main():
    # if 'user' not in session or session.get('type') != 'patient':
    #     return render_template('main_page.html', username=session['user'])
    # else:
    #     flash('You must login first!')
    #     return redirect(url_for('login'))
    if 'user' not in session or session.get('type') != 'patient':
        flash("Please log in as a patient to access this page.")
        return redirect(url_for('login'))

    return render_template('main_page.html',username=session['user'])
    
@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    # Reset session data to cancel booking
    session['appointment_mode'] = False
    session['appointment_data'] = {'location': None, 'date': None, 'time': None}
    return jsonify({'chatbot_response': "The booking process has been canceled."})

# @app.route('/view_bookings')
# def view_bookings():
#     # Fetch all bookings from the appointments table
#     try:
#         cur.execute("SELECT username, appointment_location, appointment_date, appointment_time FROM appointments ORDER BY appointment_date DESC")
#         bookings = cur.fetchall()
        
#         # Render the bookings in an HTML table
#         return render_template('view_bookings.html', bookings=bookings)
#     except Exception as e:
#         return jsonify({'error': f"Failed to fetch appointments: {str(e)}"})
    
@app.route('/chat', methods=['POST'])
def chat_with_gemini():
    user_input = request.json.get('user_input')
    user = session.get('user')

    # Check if user wants to cancel the booking
    if "cancel" in user_input.lower() and "booking" in user_input.lower():
        session['appointment_mode'] = False
        session['appointment_data'] = {'location': None, 'date': None, 'time': None}
        return jsonify({'chatbot_response': "The booking process has been canceled."})
    
     # Check if the user asks to view their appointments
    if "show" in user_input.lower() and "bookings" in user_input.lower():
        # Fetch the user's appointments from the database
        appointment_data = get_user_appointments(user)
        return jsonify({'chatbot_response': f"Here are your upcoming appointments:\n{appointment_data}"})


    # Process the rest of the conversation (chatbot's normal responses)
    response = chat.send_message(user_input)
    chatbot_response = response.text

    # Initialize session data if not set already
    if 'appointment_mode' not in session:
        session['appointment_mode'] = False
    if 'appointment_data' not in session:
        session['appointment_data'] = {'location': None, 'date': None, 'time': None}

    # Activate appointment booking if user expresses intent
    if not session['appointment_mode'] and "book" in user_input.lower() and "appointment" in user_input.lower():
        session['appointment_mode'] = True
        session['appointment_data'] = {'location': None, 'date': None, 'time': None}
        return jsonify({'chatbot_response': "Sure! Where would you like to book the appointment?"})

    # Continue with the booking process if in appointment mode
    if session['appointment_mode']:
        appointment_data = session['appointment_data']

        # Ask for location, date, and time as before
        if appointment_data['location'] is None:
            appointment_data['location'] = user_input
            session['appointment_data'] = appointment_data
            return jsonify({'chatbot_response': "Got it! What date would you like the appointment?"})

        if appointment_data['date'] is None:
            try:
                date = datetime.strptime(user_input.strip(), '%d-%m-%Y').date()
                appointment_data['date'] = date.isoformat()
                session['appointment_data'] = appointment_data
                return jsonify({'chatbot_response': "Great! What time would you prefer?"})
            except ValueError:
                return jsonify({'chatbot_response': "Please enter a valid date in DD-MM-YYYY format."})

        if appointment_data['time'] is None:
            try:
                time = datetime.strptime(user_input.strip(), '%H:%M').time()
                appointment_data['time'] = time.isoformat()
                session['appointment_data'] = appointment_data
            except ValueError:
                return jsonify({'chatbot_response': "Please enter a valid time in HH:MM format."})

        if all(appointment_data.values()):
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO appointments (username, appointment_location, appointment_date, appointment_time)
                    VALUES (%s, %s, %s, %s)
                """, (
                    user,
                    appointment_data['location'],
                    appointment_data['date'],
                    appointment_data['time']
                ))
                conn.commit()
                cur.close()

                # Reset mode and data after successful booking
                session['appointment_mode'] = False
                session['appointment_data'] = {'location': None, 'date': None, 'time': None}

                return jsonify({'chatbot_response': "✅ Your appointment has been booked successfully!"})
            except Exception as e:
                return jsonify({'chatbot_response': f"❌ Failed to book appointment: {e}"})

    # Default chatbot response
    return jsonify({'chatbot_response': chatbot_response})

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)