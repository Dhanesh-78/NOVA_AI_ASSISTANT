import sqlite3
from datetime import datetime


DB_NAME = "nova_memory.db"


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# =========================================================
# SAVE MESSAGE
# =========================================================

def save_message(role, message):

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO conversations
        (role, message, timestamp)
        VALUES (?, ?, ?)
        """,
        (
            role,
            message,
            datetime.now().isoformat()
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# GET RECENT MESSAGES
# =========================================================

def get_recent_messages(limit=10):

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT role, message
        FROM conversations
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    # Oldest → newest
    rows.reverse()

    return rows


# =========================================================
# CLEAR MEMORY
# =========================================================

def clear_memory():

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM conversations"
    )

    connection.commit()
    connection.close()