import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# NOVA MEMORY SYSTEM
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "nova_memory.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Conversation memory
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            role TEXT NOT NULL,

            content TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
        """
    )


    # --------------------------------------------------------
    # Permanent memory
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            memory TEXT NOT NULL,

            category TEXT DEFAULT 'general',

            created_at TEXT NOT NULL

        )
        """
    )


    connection.commit()

    connection.close()


# ============================================================
# SAVE CONVERSATION MESSAGE
# ============================================================

def save_message(
    role,
    content
):

    if not content:

        return

    content = str(content).strip()

    if not content:

        return


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO messages
        (
            role,
            content,
            created_at
        )

        VALUES
        (
            ?,
            ?,
            ?
        )
        """,
        (
            role,
            content,
            datetime.now().isoformat()
        )
    )


    connection.commit()

    connection.close()


# ============================================================
# GET RECENT CONVERSATION
# ============================================================

def get_recent_messages(
    limit=20
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            role,
            content,
            created_at

        FROM messages

        ORDER BY id DESC

        LIMIT ?
        """,
        (
            limit,
        )
    )


    rows = cursor.fetchall()

    connection.close()


    # Database returns newest first.
    # Reverse so Gemini receives normal conversation order.

    rows = list(
        reversed(rows)
    )


    return [
        {
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"]
        }

        for row in rows
    ]


# ============================================================
# SAVE PERMANENT MEMORY
# ============================================================

def save_memory(
    memory,
    category="general"
):

    if not memory:

        return False

    memory = str(memory).strip()

    if not memory:

        return False


    connection = get_connection()

    cursor = connection.cursor()


    # Avoid saving the exact same memory repeatedly.

    cursor.execute(
        """
        SELECT id

        FROM memories

        WHERE LOWER(memory) = LOWER(?)

        LIMIT 1
        """,
        (
            memory,
        )
    )


    existing = cursor.fetchone()


    if existing:

        connection.close()

        return False


    cursor.execute(
        """
        INSERT INTO memories
        (
            memory,
            category,
            created_at
        )

        VALUES
        (
            ?,
            ?,
            ?
        )
        """,
        (
            memory,
            category,
            datetime.now().isoformat()
        )
    )


    connection.commit()

    connection.close()

    return True


# ============================================================
# GET ALL PERMANENT MEMORIES
# ============================================================

def get_memories(
    limit=50
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            id,
            memory,
            category,
            created_at

        FROM memories

        ORDER BY id DESC

        LIMIT ?
        """,
        (
            limit,
        )
    )


    rows = cursor.fetchall()

    connection.close()


    return [
        {
            "id": row["id"],
            "memory": row["memory"],
            "category": row["category"],
            "created_at": row["created_at"]
        }

        for row in rows
    ]


# ============================================================
# SEARCH PERMANENT MEMORY
# ============================================================

def search_memories(
    keyword
):

    if not keyword:

        return []


    keyword = str(keyword).strip()

    if not keyword:

        return []


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            id,
            memory,
            category,
            created_at

        FROM memories

        WHERE memory LIKE ?

        ORDER BY id DESC
        """,
        (
            f"%{keyword}%",
        )
    )


    rows = cursor.fetchall()

    connection.close()


    return [
        {
            "id": row["id"],
            "memory": row["memory"],
            "category": row["category"],
            "created_at": row["created_at"]
        }

        for row in rows
    ]


# ============================================================
# DELETE ONE MEMORY
# ============================================================

def delete_memory(
    memory_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        DELETE FROM memories

        WHERE id = ?
        """,
        (
            memory_id,
        )
    )


    deleted = cursor.rowcount > 0


    connection.commit()

    connection.close()


    return deleted


# ============================================================
# CLEAR CONVERSATION MEMORY
# ============================================================

def clear_conversation():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        DELETE FROM messages
        """
    )


    connection.commit()

    connection.close()


# ============================================================
# CLEAR PERMANENT MEMORY
# ============================================================

def clear_permanent_memory():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        DELETE FROM memories
        """
    )


    connection.commit()

    connection.close()


# ============================================================
# CLEAR EVERYTHING
# ============================================================

def clear_memory():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        DELETE FROM messages
        """
    )


    cursor.execute(
        """
        DELETE FROM memories
        """
    )


    connection.commit()

    connection.close()


# ============================================================
# MEMORY SUMMARY
# ============================================================

def get_memory_summary():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT COUNT(*)
        FROM messages
        """
    )

    message_count = cursor.fetchone()[0]


    cursor.execute(
        """
        SELECT COUNT(*)
        FROM memories
        """
    )

    memory_count = cursor.fetchone()[0]


    connection.close()


    return {
        "conversation_messages": message_count,
        "permanent_memories": memory_count
    }


# ============================================================
# INITIALIZE DATABASE WHEN MODULE LOADS
# ============================================================

init_db()