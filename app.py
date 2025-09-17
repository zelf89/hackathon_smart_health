from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from dotenv import load_dotenv
import os
import google.generativeai as genai

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

# Create the model and start a chat session
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

print("Hello! I'm your Gemini chatbot. Type 'exit' to end the conversation.")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("Chatbot: Goodbye!")
        break
    
    # Send user input to the Gemini model and get a response
    try:
        response = chat.send_message(user_input)
        print("Chatbot:", response.text)
    except Exception as e:
        print(f"An error occurred: {e}")

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

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)