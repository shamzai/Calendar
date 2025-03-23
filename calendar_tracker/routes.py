from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from services.gemini_service import GeminiService
from utils import get_db_connection, analyze_sentiment

main_bp = Blueprint('main', __name__)
gemini_service = GeminiService()

@main_bp.route('/')
def index():
    """Render the main page with today's date"""
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', today_date=today)

@main_bp.route('/addHabit', methods=['POST'])
def add_habit():
    """Add a new habit with enhanced tracking and event features"""
    date = request.form.get('date')
    habit = request.form.get('habit')
    start_time = request.form.get('start_time', '').strip() or None
    end_time = request.form.get('end_time', '').strip() or None
    description = request.form.get('description')
    category = request.form.get('category', 'default')
    priority = request.form.get('priority', 1)
    recurrence = request.form.get('recurrence')
    reminder = request.form.get('reminder')
    color = request.form.get('color')

    if not date or not habit:
        return "Missing required fields.", 400

    if start_time and end_time:
        try:
            datetime.strptime(start_time, '%H:%M')
            datetime.strptime(end_time, '%H:%M')
        except ValueError:
            return "Invalid time format.", 400

    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO habits (
                    date, habit, start_time, end_time, description,
                    category, priority, color, recurrence_pattern, reminder_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date, habit, start_time, end_time, description,
                category, priority, color, recurrence, reminder
            ))
            habit_id = c.lastrowid
            
            c.execute("""
                INSERT INTO habit_tracking (habit_id, tracked_date)
                VALUES (?, date('now'))
            """, (habit_id,))
            conn.commit()
            
            event = {
                'id': habit_id,
                'title': habit,
                'allDay': not (start_time and end_time),
                'start': f"{date}T{start_time}" if start_time else date,
                'end': f"{date}T{end_time}" if end_time else None,
                'backgroundColor': color or ('#1e40af' if start_time and end_time else '#3b82f6'),
                'borderColor': color or ('#1e3a8a' if start_time and end_time else '#2563eb'),
                'textColor': 'white',
                'description': description,
                'category': category,
                'priority': priority,
                'recurrence': recurrence,
                'reminder': reminder,
                'extendedProps': {
                    'category': category,
                    'priority': priority
                }
            }
            return jsonify(event), 200
        except Exception as e:
            return str(e), 500

@main_bp.route('/updateHabit', methods=['POST'])
def update_habit():
    """Update an existing habit's details"""
    habit_id = request.form.get('id')
    habit = request.form.get('habit')
    description = request.form.get('description')
    category = request.form.get('category')
    priority = request.form.get('priority')
    color = request.form.get('color')
    
    if not habit_id or not habit:
        return "Missing required fields.", 400
        
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("""
                UPDATE habits 
                SET habit = ?, description = ?, category = ?, 
                    priority = ?, color = ?, last_modified = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (habit, description, category, priority, color, habit_id))
            conn.commit()
            
            # Return updated event data
            c.execute("""
                SELECT date, start_time, end_time, description, category, priority, color
                FROM habits WHERE id = ?
            """, (habit_id,))
            row = c.fetchone()
            
            if not row:
                return "Habit not found.", 404
                
            date, start_time, end_time, desc, cat, prio, col = row
            event = {
                'id': habit_id,
                'title': habit,
                'allDay': not (start_time and end_time),
                'start': f"{date}T{start_time}" if start_time else date,
                'end': f"{date}T{end_time}" if end_time else None,
                'backgroundColor': col or ('#1e40af' if start_time and end_time else '#3b82f6'),
                'borderColor': col or ('#1e3a8a' if start_time and end_time else '#2563eb'),
                'textColor': 'white',
                'description': desc,
                'category': cat,
                'priority': prio,
                'extendedProps': {
                    'category': cat,
                    'priority': prio
                }
            }
            return jsonify(event), 200
        except Exception as e:
            return str(e), 500

@main_bp.route('/rescheduleHabit', methods=['POST'])
def reschedule_habit():
    """Reschedule a habit to a new date/time"""
    habit_id = request.form.get('id')
    new_date = request.form.get('date')
    new_start = request.form.get('start_time', '').strip() or None
    new_end = request.form.get('end_time', '').strip() or None
    
    if not habit_id or not new_date:
        return "Missing required fields.", 400
        
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("""
                UPDATE habits 
                SET date = ?, start_time = ?, end_time = ?, 
                    last_modified = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_date, new_start, new_end, habit_id))
            conn.commit()
            
            # Return updated event data
            c.execute("SELECT habit FROM habits WHERE id = ?", (habit_id,))
            habit = c.fetchone()[0]
            
            event = {
                'id': habit_id,
                'title': habit,
                'allDay': not (new_start and new_end),
                'start': f"{new_date}T{new_start}" if new_start else new_date,
                'end': f"{new_date}T{new_end}" if new_end else None,
            }
            return jsonify(event), 200
        except Exception as e:
            return str(e), 500

@main_bp.route('/removeHabit', methods=['POST'])
def remove_habit():
    """Delete a habit and its associated data"""
    habit_id = request.form.get('id')
    
    if not habit_id:
        return "Missing habit ID.", 400
        
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            # Delete associated tracking records first
            c.execute("DELETE FROM habit_tracking WHERE habit_id = ?", (habit_id,))
            # Then delete the habit
            c.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            conn.commit()
            return jsonify({'message': 'Habit deleted successfully'}), 200
        except Exception as e:
            return str(e), 500

@main_bp.route('/habits', methods=['GET'])
def get_habits():
    """Get all habits for calendar display with extended properties and filtering"""
    filters = {
        'category': request.args.get('category'),
        'priority': request.args.get('priority'),
        'start': request.args.get('start'),
        'end': request.args.get('end'),
        'search': request.args.get('search')
    }
    
    query = """
        SELECT id, date, habit, start_time, end_time, description,
               category, priority, color, recurrence_pattern, reminder_time,
               completed
        FROM habits
        WHERE 1=1
    """
    params = []
    
    # Apply filters
    if filters['category']:
        query += " AND category = ?"
        params.append(filters['category'])
    
    if filters['priority']:
        query += " AND priority = ?"
        params.append(filters['priority'])
    
    if filters['start']:
        query += " AND date >= ?"
        params.append(filters['start'])
    
    if filters['end']:
        query += " AND date <= ?"
        params.append(filters['end'])
    
    if filters['search']:
        query += " AND (habit LIKE ? OR description LIKE ?)"
        search_term = f"%{filters['search']}%"
        params.extend([search_term, search_term])

    # Add sorting
    query += " ORDER BY date ASC, start_time ASC"

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        data = c.fetchall()

    habits = []
    for row in data:
        (habit_id, habit_date, habit_text, start_time, end_time, description,
         category, priority, color, recurrence, reminder) = row
        
        event = {
            'id': habit_id,
            'title': habit_text,
            'allDay': not (start_time and end_time),
            'start': f"{habit_date}T{start_time}" if start_time else habit_date,
            'end': f"{habit_date}T{end_time}" if end_time else None,
            'backgroundColor': color or ('#1e40af' if start_time and end_time else '#3b82f6'),
            'borderColor': color or ('#1e3a8a' if start_time and end_time else '#2563eb'),
            'textColor': 'white',
            'description': description,
            'category': category,
            'priority': priority,
            'recurrence': recurrence,
            'reminder': reminder,
            'extendedProps': {
                'category': category,
                'priority': priority
            }
        }
        habits.append(event)

    return jsonify(habits)

@main_bp.route('/chat', methods=['POST'])
def chat():
    """Enhanced chatbot with Gemini AI and context awareness"""
    data = request.get_json()
    message = data.get('message', '').lower()
    
    with get_db_connection() as conn:
        c = conn.cursor()
        today = datetime.now().date()

        # Get user's habits for context
        c.execute("""
            SELECT habit FROM habits 
            WHERE date >= date('now', '-7 days')
            GROUP BY habit
        """)
        user_habits = [row[0] for row in c.fetchall()]

        # Get progress data
        try:
            c.execute("SELECT completed FROM habits LIMIT 1")
        except sqlite3.OperationalError:
            # Add completed column if it doesn't exist
            c.execute("ALTER TABLE habits ADD COLUMN completed INTEGER DEFAULT 0")
            conn.commit()

        c.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
            FROM habits 
            WHERE date >= date('now', '-7 days')
        """)
        total, completed = c.fetchone()
        
    # Format progress info
    progress = None
    if total > 0:
        completion_rate = (completed / total * 100) if completed else 0
        progress = f"Completed {completed}/{total} habits ({completion_rate:.1f}% success rate) in the past week"

    # Get AI response with context
    try:
        response = gemini_service.get_response(
            message=message,
            user_habits=user_habits,
            progress=progress
        )
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({
            'response': "I apologize, but I'm having trouble responding right now. Please try again. 🙏"
        }), 500
