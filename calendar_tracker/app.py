from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import re

app = Flask(__name__)

def init_db():
    """
    Initialize the SQLite database and create the 'habits' table if it doesn't exist.
    """
    conn = sqlite3.connect('habits.db')
    c = conn.cursor()
    # Create table with NOT NULL constraints for date and habit if desired
    c.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            habit TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """
    Renders the main page (index.html).
    """
    return render_template('index.html')

@app.route('/addHabit', methods=['POST'])
def add_habit():
    """
    Inserts a new habit record into the database.
    Expects 'date' and 'habit' from a POST request.
    """
    date = request.form.get('date')
    habit = request.form.get('habit')

    # Optional: Check for empty fields (basic validation)
    if not date or not habit:
        return "Missing 'date' or 'habit' field.", 400

    conn = sqlite3.connect('habits.db')
    c = conn.cursor()
    c.execute("INSERT INTO habits (date, habit) VALUES (?, ?)", (date, habit))
    conn.commit()
    conn.close()

    return "Habit added!", 200

@app.route('/habits', methods=['GET'])
def get_habits():
    """
    Fetches all habits from the database and returns them
    in a JSON format compatible with FullCalendar:
    [
      {
        'id': <int>,
        'start': <YYYY-MM-DD string>,
        'title': <string>
      },
      ...
    ]

    Note: 'title' is how FullCalendar displays text on the calendar.
    Internally, we store it in the 'habit' column.
    """
    conn = sqlite3.connect('habits.db')
    c = conn.cursor()
    c.execute("SELECT id, date, habit FROM habits")
    data = c.fetchall()
    conn.close()

    habits = []
    for row in data:
        habit_id, habit_date, habit_text = row
        habits.append({
            'id': habit_id,       # Unique ID for FullCalendar
            'start': habit_date,  # The date for FullCalendar (YYYY-MM-DD)
            'title': habit_text   # Displayed on the calendar
        })

    return jsonify(habits)

@app.route('/removeHabit', methods=['POST'])
def remove_habit():
    """
    Removes a habit from the database by its 'id' field.
    Expects 'id' from a POST request.
    """
    habit_id = request.form.get('id')
    if not habit_id:
        return "Missing 'id' field.", 400

    conn = sqlite3.connect('habits.db')
    c = conn.cursor()
    c.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()

    return "Habit removed!", 200

@app.route('/updateHabit', methods=['POST'])
def update_habit():
    """
    Updates an existing habit record in the database.
    Expects 'id', 'date', and 'title' from a POST request.
    - 'id': The unique ID of the record to update
    - 'date': The new date (YYYY-MM-DD)
    - 'title': The new habit text (FullCalendar uses 'title' for the event text)
    
    We map 'title' to the 'habit' column in the database.
    """
    habit_id = request.form.get('id')
    new_date = request.form.get('date')
    new_habit = request.form.get('title')  # Rename for clarity

    if not habit_id or not new_date or not new_habit:
        return "Missing 'id', 'date', or 'title' field.", 400

    conn = sqlite3.connect('habits.db')
    c = conn.cursor()
    c.execute("UPDATE habits SET date = ?, habit = ? WHERE id = ?", 
              (new_date, new_habit, habit_id))
    conn.commit()
    conn.close()

    return "Habit updated!", 200

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handles chat messages and provides responses based on habit data.
    Expects a JSON payload with a 'message' field.
    """
    data = request.get_json()
    message = data.get('message', '').lower()

    # Connect to database
    conn = sqlite3.connect('habits.db')
    c = conn.cursor()

    # Get current date for relative queries
    today = datetime.now().date()
    
    # Define response based on message content
    if 'show' in message and 'habits' in message:
        # Show recent habits
        c.execute("SELECT date, habit FROM habits ORDER BY date DESC LIMIT 5")
        habits = c.fetchall()
        if habits:
            response = "Here are your recent habits:\n"
            for date, habit in habits:
                response += f"- {habit} on {date}\n"
        else:
            response = "You haven't tracked any habits yet."

    elif 'streak' in message or 'consistent' in message:
        # Find habits with streaks (consecutive days)
        c.execute("""
            SELECT habit, COUNT(*) as count 
            FROM habits 
            GROUP BY habit 
            ORDER BY count DESC 
            LIMIT 1
        """)
        result = c.fetchone()
        if result:
            habit, count = result
            response = f"Your most consistent habit is '{habit}' with {count} entries!"
        else:
            response = "Start tracking habits to see your streaks!"

    elif 'today' in message:
        # Show today's habits
        c.execute("SELECT habit FROM habits WHERE date = ?", (today.strftime('%Y-%m-%d'),))
        habits = c.fetchall()
        if habits:
            response = "Today's habits:\n" + "\n".join([f"- {h[0]}" for h in habits])
        else:
            response = "No habits tracked for today yet. Would you like to add one?"

    elif 'help' in message:
        response = """I can help you with:
- Showing your recent habits
- Checking your habit streaks
- Viewing today's habits
- Getting suggestions for new habits
Just ask me what you'd like to know!"""

    elif 'suggest' in message or 'recommendation' in message:
        # Get user's existing habits for context
        c.execute("SELECT DISTINCT habit FROM habits")
        existing_habits = {row[0].lower() for row in c.fetchall()}
        
        suggestions = [
            "Morning meditation",
            "Daily exercise",
            "Reading",
            "Drinking water",
            "Healthy breakfast",
            "Evening walk",
            "Journaling",
            "Learning something new"
        ]
        
        # Filter out habits the user already has
        new_suggestions = [s for s in suggestions if s.lower() not in existing_habits][:3]
        
        if new_suggestions:
            response = "Here are some habit suggestions you might like:\n"
            response += "\n".join([f"- {habit}" for habit in new_suggestions])
        else:
            response = "You're already tracking a great variety of habits! Keep it up!"

    else:
        response = "I'm here to help you with your habits! You can ask me to:\n"
        response += "- Show your recent habits\n"
        response += "- Check your streaks\n"
        response += "- View today's habits\n"
        response += "- Get habit suggestions"

    conn.close()
    return jsonify({'response': response})

if __name__ == '__main__':
    init_db()  # Ensure the database and table are initialized
    app.run(debug=True)
