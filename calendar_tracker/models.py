import sqlite3
from utils import get_db_connection
from datetime import datetime

def init_db():
    """Initialize the database with enhanced tracking and chat capabilities"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Core habits table with advanced event features
        c.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                habit TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                completed BOOLEAN DEFAULT 0,
                description TEXT,
                category TEXT DEFAULT 'default',
                priority INTEGER DEFAULT 1,
                color TEXT,
                recurrence_pattern TEXT,
                reminder_time TEXT,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tracking table with enhanced analytics
        c.execute('''
            CREATE TABLE IF NOT EXISTS habit_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                tracked_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )
        ''')

        # Chat history for context-aware conversations
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Calendar events for better scheduling
        c.execute('''
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                start_datetime TIMESTAMP NOT NULL,
                end_datetime TIMESTAMP,
                all_day BOOLEAN DEFAULT 0,
                recurrence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )
        ''')
        
        conn.commit()

def migrate_existing_data():
    """Migrate existing habits to new calendar events table"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Get all habits with dates and times
        c.execute('''
            SELECT id, date, habit, start_time, end_time
            FROM habits
            WHERE date IS NOT NULL
        ''')
        
        habits = c.fetchall()
        
        for habit in habits:
            habit_id, date, title, start_time, end_time = habit
            
            # Convert date and times to proper datetime
            start_datetime = f"{date} {start_time}" if start_time else f"{date} 00:00:00"
            end_datetime = f"{date} {end_time}" if end_time else f"{date} 23:59:59"
            
            # Insert into calendar_events
            c.execute('''
                INSERT INTO calendar_events 
                (habit_id, title, start_datetime, end_datetime, all_day)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                habit_id,
                title,
                start_datetime,
                end_datetime,
                1 if not (start_time and end_time) else 0
            ))
        
        conn.commit()
