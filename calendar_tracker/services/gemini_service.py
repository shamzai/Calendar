import os
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
import sqlite3
from utils import get_db_connection
import re

load_dotenv()

class GeminiService:
    # Enhanced static responses with calendar integration
    FALLBACK_RESPONSES = {
        'greetings': {
            'morning': [
                "Good morning! Ready to make today amazing? ☀️",
                "Rise and shine! How can I help you start your day right? 🌅"
            ],
            'afternoon': [
                "Good afternoon! How's your day going? 🌤️",
                "Hope you're having a great day! What can I help you with? 💫"
            ],
            'evening': [
                "Good evening! Let's review your day together. 🌙",
                "Evening! How did your habits go today? ⭐"
            ]
        },
        'schedule': {
            'success': "I've scheduled that for you! 📅",
            'error': "I couldn't schedule that. Please try again with a specific time and date. ⚠️",
            'conflict': "There's already something scheduled for that time. Would you like to choose another time? 🤔"
        },
        'encouragement': {
            'streak': "You're on fire! Keep that streak going! 🔥",
            'recovery': "Tomorrow is a new day - you've got this! 🌅",
            'achievement': "Amazing work! You're crushing it! 🎉"
        },
        'motivation': {
            'general': "You've got this! One step at a time! 🌟"
        }
    }

    # Calendar command patterns
    CALENDAR_PATTERNS = {
        'schedule': r'(?i)(schedule|plan|add|create|set up)\s+(an?\s+)?(?P<habit>.*?)\s+(for|on|at)\s+(?P<datetime>.*)',
        'move': r'(?i)(move|reschedule|change)\s+(?P<habit>.*?)\s+to\s+(?P<datetime>.*)',
        'cancel': r'(?i)(cancel|delete|remove)\s+(?P<habit>.*?)(\s+on\s+(?P<date>.*))?',
        'list': r'(?i)(show|list|what are)\s+(my\s+)?(tasks|habits|events|schedule)(\s+for\s+(?P<date>.*))?'
    }

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        if not self.validate_api_key(self.api_key):
            raise ValueError("Invalid Gemini API key format")

        try:
            # Configure with safety settings
            genai.configure(api_key=self.api_key)
            
            # List available models first
            try:
                models = genai.list_models()
                available_models = [m.name for m in models]
                print(f"Available models: {available_models}")
                
                if "models/gemini-pro" not in available_models:
                    raise Exception("gemini-pro model not available")
                    
            except Exception as e:
                print(f"Error listing models: {str(e)}")
                raise Exception("Unable to access Gemini API models")
            
            # Initialize with safety settings
            generation_config = {
                "temperature": 0.9,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            self.model = genai.GenerativeModel(
                model_name="gemini-pro",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Test connection with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    test_response = self.model.generate_content("Test connection")
                    if test_response and test_response.text:
                        print(f"API Test successful (attempt {attempt + 1}): {test_response.text[:50]}...")
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"Attempt {attempt + 1} failed, retrying...")
            
            self.chat = self.model.start_chat(history=[])
            self.use_fallback = False
            self.load_chat_history()
            print("Successfully initialized Gemini AI service")
            
        except Exception as e:
            self.log_error("Error initializing Gemini AI", e)
            self.use_fallback = True
            raise RuntimeError(f"Failed to initialize Gemini AI: {str(e)}")

    def validate_api_key(self, key):
        """Validate Gemini API key format"""
        # TODO: Implement stricter validation when in production
        if not key or len(key) < 10:  # Basic check to ensure key exists and has minimum length
            return False
        return True
        
    def log_error(self, message, error=None):
        """Log errors with detailed information"""
        error_msg = f"[{datetime.now()}] {message}"
        if error:
            error_msg += f": {str(error)}"
            if hasattr(error, 'details'):
                error_msg += f"\nDetails: {error.details}"
                
        print(error_msg)  # In production, use proper logging
        
        try:
            with open('gemini_errors.log', 'a') as f:
                f.write(error_msg + '\n')
        except:
            pass  # Fail silently if can't write to log file

    def load_chat_history(self, limit=10):
        """Load recent chat history for context"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT user_message, bot_response, context
                    FROM chat_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                history = c.fetchall()
                
                # Add to Gemini chat history
                for user_msg, bot_resp, _ in history[::-1]:  # Reverse to maintain chronological order
                    self.chat.history.append({"role": "user", "parts": [user_msg]})
                    self.chat.history.append({"role": "model", "parts": [bot_resp]})
        except Exception as e:
            print(f"Error loading chat history: {str(e)}")

    def get_time_of_day(self):
        """Get the time of day category and formatted time"""
        current = datetime.now()
        hour = current.hour
        if 5 <= hour < 12:
            period = 'morning'
        elif 12 <= hour < 17:
            period = 'afternoon'
        else:
            period = 'evening'
        return period, current.strftime('%I:%M %p')

    def get_context(self, user_habits=None, progress=None):
        """Build enhanced context including calendar information"""
        period, current_time = self.get_time_of_day()
        today = datetime.now().date()

        context = f"""
        You are an intelligent AI assistant for a calendar and habit tracking application.
        Current time: {current_time}
        Time of day: {period}
        """

        # Add calendar events
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT title, start_datetime, end_datetime
                    FROM calendar_events
                    WHERE date(start_datetime) = date('now')
                    ORDER BY start_datetime
                """)
                events = c.fetchall()
                
                if events:
                    context += "\n\nToday's schedule:"
                    for title, start, end in events:
                        context += f"\n- {title}: {start} - {end}"

        except Exception as e:
            print(f"Error getting calendar context: {str(e)}")

        if user_habits:
            context += f"\n\nUser's tracked habits: {', '.join(user_habits)}"
        if progress:
            context += f"\nRecent progress: {progress}"

        return context

    def get_greeting(self):
        """Get an enhanced context-aware greeting"""
        period, _ = self.get_time_of_day()
        greetings = self.FALLBACK_RESPONSES['greetings'][period]
        return greetings[0] if greetings else "Hello! 👋"

    def parse_datetime(self, datetime_str):
        """Parse natural language datetime into structured format"""
        now = datetime.now()
        datetime_str = datetime_str.lower().strip()
        
        # Common datetime patterns
        patterns = {
            'today': now.date(),
            'tomorrow': now.date() + timedelta(days=1),
            'next week': now.date() + timedelta(weeks=1)
        }
        
        # Handle relative days
        if datetime_str in patterns:
            return patterns[datetime_str]
            
        # TODO: Add more sophisticated datetime parsing
        # For now, expect ISO format or simple patterns
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d')
        except ValueError:
            try:
                return datetime.strptime(datetime_str, '%I:%M %p')
            except ValueError:
                return None

    def handle_calendar_command(self, message):
        """Process calendar-related commands"""
        for command, pattern in self.CALENDAR_PATTERNS.items():
            match = re.match(pattern, message)
            if match:
                try:
                    if command == 'schedule':
                        habit = match.group('habit')
                        dt = self.parse_datetime(match.group('datetime'))
                        if dt:
                            return self.schedule_habit(habit, dt)
                        return self.FALLBACK_RESPONSES['schedule']['error']
                    
                    elif command == 'move':
                        habit = match.group('habit')
                        new_dt = self.parse_datetime(match.group('datetime'))
                        if new_dt:
                            return self.reschedule_habit(habit, new_dt)
                        return "Please specify a valid date and time for rescheduling."
                    
                    elif command == 'cancel':
                        habit = match.group('habit')
                        date = match.group('date')
                        return self.cancel_habit(habit, date)
                    
                    elif command == 'list':
                        date = match.group('date')
                        return self.list_schedule(date)
                        
                except Exception as e:
                    print(f"Error handling calendar command: {str(e)}")
                    return "Sorry, I couldn't process that calendar operation. Please try again."
        
        return None  # Not a calendar command

    def get_response(self, message, user_habits=None, progress=None):
        """Generate an enhanced response with calendar integration"""
        if hasattr(self, 'use_fallback') and self.use_fallback:
            return self._get_fallback_response(message, user_habits, progress)
            
        try:
            # First check for calendar commands
            calendar_response = self.handle_calendar_command(message)
            if calendar_response:
                return calendar_response

            context = self.get_context(user_habits, progress)
            
            # Prepare prompt
            prompt = f"""
            Context: {context}
            
            Chat History:
            {self.format_chat_history()}
            
            User message: {message}
            
            Remember to:
            1. Be encouraging and supportive
            2. Reference specific habits and schedule when relevant
            3. Provide actionable suggestions
            4. Keep responses concise but helpful
            5. Use emojis occasionally to keep the tone friendly
            6. Offer to schedule habits when appropriate
            """

            # Generate response
            response = self.model.generate_content(prompt)
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
                
            response_text = response.text
            self.save_chat_history(message, response_text, context)
            return response_text

        except Exception as e:
            error_msg = f"Error in Gemini service: {str(e)}"
            self.log_error(error_msg, e)
            
            if "quota exceeded" in str(e).lower():
                return "I'm currently busy with too many requests. Please try again in a moment. ⏳"
            elif "invalid api key" in str(e).lower():
                return "There seems to be an issue with my configuration. Please contact support. ⚠️"
            else:
                return self._get_fallback_response(message, user_habits, progress)

    def schedule_habit(self, habit, dt):
        """Schedule a new habit in the calendar"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                
                # Check for conflicts
                c.execute("""
                    SELECT COUNT(*) FROM calendar_events
                    WHERE date(start_datetime) = date(?)
                    AND time(start_datetime) = time(?)
                """, (dt, dt))
                
                if c.fetchone()[0] > 0:
                    return self.FALLBACK_RESPONSES['schedule']['conflict']
                
                # Add the habit
                c.execute("""
                    INSERT INTO habits (date, habit)
                    VALUES (date(?), ?)
                """, (dt, habit))
                habit_id = c.lastrowid
                
                # Create calendar event
                c.execute("""
                    INSERT INTO calendar_events 
                    (habit_id, title, start_datetime)
                    VALUES (?, ?, ?)
                """, (habit_id, habit, dt))
                
                conn.commit()
                return self.FALLBACK_RESPONSES['schedule']['success']
                
        except Exception as e:
            print(f"Error scheduling habit: {str(e)}")
            return self.FALLBACK_RESPONSES['schedule']['error']

    def reschedule_habit(self, habit, new_dt):
        """Move an existing habit to a new date/time"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                
                # Find the habit
                c.execute("""
                    SELECT ce.id, ce.habit_id 
                    FROM calendar_events ce
                    JOIN habits h ON h.id = ce.habit_id
                    WHERE h.habit LIKE ?
                    ORDER BY ce.start_datetime DESC
                    LIMIT 1
                """, (f'%{habit}%',))
                
                result = c.fetchone()
                if not result:
                    return "I couldn't find that habit. Please check the name and try again."
                
                event_id, habit_id = result
                
                # Check for conflicts at new time
                c.execute("""
                    SELECT COUNT(*) FROM calendar_events
                    WHERE date(start_datetime) = date(?)
                    AND time(start_datetime) = time(?)
                    AND id != ?
                """, (new_dt, new_dt, event_id))
                
                if c.fetchone()[0] > 0:
                    return self.FALLBACK_RESPONSES['schedule']['conflict']
                
                # Update both habit and calendar event
                c.execute("""
                    UPDATE habits 
                    SET date = date(?)
                    WHERE id = ?
                """, (new_dt, habit_id))
                
                c.execute("""
                    UPDATE calendar_events
                    SET start_datetime = ?
                    WHERE id = ?
                """, (new_dt, event_id))
                
                conn.commit()
                return f"Successfully rescheduled '{habit}' to {new_dt.strftime('%Y-%m-%d %I:%M %p')} 📅"
                
        except Exception as e:
            print(f"Error rescheduling habit: {str(e)}")
            return "Sorry, I couldn't reschedule that habit. Please try again."

    def cancel_habit(self, habit, date=None):
        """Cancel/delete a habit from the calendar"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                
                # Build query based on whether date is specified
                query = """
                    DELETE FROM calendar_events 
                    WHERE id IN (
                        SELECT ce.id
                        FROM calendar_events ce
                        JOIN habits h ON h.id = ce.habit_id
                        WHERE h.habit LIKE ?
                """
                params = [f'%{habit}%']
                
                if date:
                    query += " AND date(ce.start_datetime) = date(?)"
                    params.append(date)
                    
                query += " LIMIT 1)"
                
                c.execute(query, params)
                
                if c.rowcount > 0:
                    conn.commit()
                    return f"Successfully cancelled '{habit}' ✅"
                return f"I couldn't find '{habit}' in your calendar."
                
        except Exception as e:
            print(f"Error cancelling habit: {str(e)}")
            return "Sorry, I couldn't cancel that habit. Please try again."

    def list_schedule(self, date=None):
        """List habits scheduled for a specific date"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                
                if date:
                    try:
                        target_date = self.parse_datetime(date)
                        if not target_date:
                            return "Please provide a valid date."
                    except ValueError:
                        return "Please provide a valid date format."
                else:
                    target_date = datetime.now().date()
                
                c.execute("""
                    SELECT h.habit, 
                           ce.start_datetime,
                           ce.end_datetime,
                           ce.all_day
                    FROM calendar_events ce
                    JOIN habits h ON h.id = ce.habit_id
                    WHERE date(ce.start_datetime) = date(?)
                    ORDER BY ce.start_datetime
                """, (target_date,))
                
                events = c.fetchall()
                
                if not events:
                    return f"No habits scheduled for {target_date.strftime('%Y-%m-%d')} 📅"
                
                response = f"Schedule for {target_date.strftime('%Y-%m-%d')} 📅\n"
                for habit, start, end, all_day in events:
                    if all_day:
                        response += f"\n• {habit} (all day)"
                    else:
                        start_time = datetime.strptime(start, '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p')
                        if end:
                            end_time = datetime.strptime(end, '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p')
                            response += f"\n• {habit} ({start_time} - {end_time})"
                        else:
                            response += f"\n• {habit} (at {start_time})"
                
                return response
                
        except Exception as e:
            print(f"Error listing schedule: {str(e)}")
            return "Sorry, I couldn't retrieve the schedule. Please try again."

    def format_chat_history(self, limit=5):
        """Format recent chat history for context"""
        if not self.chat.history:
            return "No previous conversation."
            
        formatted = "Recent conversation:\n"
        for i in range(-min(len(self.chat.history), limit*2), 0, 2):
            user_msg = self.chat.history[i]["parts"][0]
            bot_resp = self.chat.history[i+1]["parts"][0]
            formatted += f"User: {user_msg}\nAssistant: {bot_resp}\n"
        return formatted

    def save_chat_history(self, user_message, bot_response, context):
        """Save chat interaction to database"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO chat_history 
                    (user_message, bot_response, context)
                    VALUES (?, ?, ?)
                """, (user_message, bot_response, context))
                conn.commit()
        except Exception as e:
            print(f"Error saving chat history: {str(e)}")

    def get_encouragement(self, sentiment='neutral', context=None):
        """Generate enhanced contextual encouragement with schedule awareness"""
        try:
            if not self.use_fallback:
                # Get upcoming events for context
                upcoming_events = []
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("""
                        SELECT title, start_datetime
                        FROM calendar_events
                        WHERE start_datetime > datetime('now')
                        ORDER BY start_datetime
                        LIMIT 1
                    """)
                    upcoming = c.fetchone()
                    if upcoming:
                        upcoming_events.append(upcoming)

                prompt = f"""
                Generate an encouraging message for a habit tracking app user.
                Sentiment: {sentiment}
                Context: {context if context else 'General encouragement'}
                
                {f"Upcoming event: {upcoming_events[0][0]} at {upcoming_events[0][1]}" if upcoming_events else ""}
                
                Keep it:
                1. Brief (1-2 sentences)
                2. Positive and supportive
                3. Reference upcoming events if available
                4. Include one relevant emoji
                """

                response = self.model.generate_content(prompt)
                return response.text.strip()

        except Exception as e:
            print(f"Error generating encouragement: {str(e)}")
            
        # Enhanced fallback responses
        if context == 'streak':
            return self.FALLBACK_RESPONSES['encouragement']['streak']
        elif sentiment == 'negative':
            return self.FALLBACK_RESPONSES['encouragement']['recovery']
        elif context == 'achievement':
            return self.FALLBACK_RESPONSES['encouragement']['achievement']
        return self.FALLBACK_RESPONSES['motivation']['general']

    def _get_fallback_response(self, message, user_habits=None, progress=None):
        """Generate static fallback responses when API is unavailable"""
        message = message.lower()
        
        # Check for greetings
        if any(word in message for word in ['hello', 'hi', 'hey', 'good']):
            return self.get_greeting()
            
        # Check for schedule-related queries
        if any(word in message for word in ['schedule', 'plan', 'calendar', 'event']):
            return "I can help you schedule habits and events, but I need some maintenance first. Please try again later. 🔧"
            
        # Check for progress/motivation queries
        if any(word in message for word in ['progress', 'track', 'goal', 'achievement']):
            if progress and 'completed' in progress.lower():
                return self.FALLBACK_RESPONSES['encouragement']['achievement']
            return self.FALLBACK_RESPONSES['motivation']['general']
            
        # Default response
        return "I'm having trouble connecting to my main system, but I'm still here to help with basic tasks! What would you like to do? 🤖"
