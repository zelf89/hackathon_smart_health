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

@app.route('/', methods=['GET', 'POST'])
def login():

    if 'user' in session:
        return redirect(url_for('main'))
       
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username,password))
        result = cur.fetchone()
        cur.close()
        
        if result:
            session['user'] = username
            return redirect(url_for('main'))
        else:
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('login'))
           
    return render_template('login_page.html')

@app.route('/main')
def main():
    if 'user' in session:
        return render_template('main_page.html', username=session['user'])
    else:
        flash('You must login first!')
        return redirect(url_for('login'))
    
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