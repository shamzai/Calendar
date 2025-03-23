from contextlib import contextmanager
import sqlite3
from datetime import datetime

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = sqlite3.connect('habits.db')
    try:
        yield conn
    finally:
        conn.close()

def analyze_sentiment(message):
    """Analyze message sentiment using keyword matching"""
    positive_words = {'great', 'good', 'happy', 'excited', 'love', 'awesome', 'amazing', 'wonderful'}
    negative_words = {'bad', 'sad', 'tired', 'cant', "can't", 'hard', 'difficult', 'struggling'}
    uncertain_words = {'maybe', 'try', 'might', 'not sure', 'confused', 'help', 'unsure'}
    
    words = set(message.lower().split())
    
    if words & positive_words:
        return 'positive'
    elif words & negative_words:
        return 'negative'
    elif words & uncertain_words:
        return 'uncertain'
    return 'neutral'
