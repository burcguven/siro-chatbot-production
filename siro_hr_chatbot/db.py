import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "1701603bG!"),
        database=os.getenv("DB_NAME", "chatbot_db")
    )

def authenticate_user(email_addr, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
        SELECT 
            u.mail,
            ea.acc_id
        FROM employee_accounts ea
        JOIN employees e ON ea.emp_id = e.emp_id
        JOIN users u ON e.user_id = u.user_id
        WHERE u.mail = %s
        """
        cursor.execute(query, (email_addr,))
        row = cursor.fetchone()

        if row is None:
            return None

        mock_password = os.getenv("MOCK_PASSWORD_FOR_EVERYONE")
        if not mock_password:
            raise RuntimeError("MOCK_PASSWORD_FOR_EVERYONE .env içinde tanımlı değil")

        if password != mock_password:
            return None

        return {
            "email": row["mail"],
            "acc_id": row["acc_id"]
        }

    finally:
        cursor.close()
        conn.close()

def get_account_id(conn, email_addr):  # get employee account id from email

    query = """
    SELECT ea.acc_id
    FROM employee_accounts ea
    JOIN employees e ON ea.emp_id = e.emp_id
    JOIN users u ON e.user_id = u.user_id
    WHERE u.mail = %s
    """
    cursor = conn.cursor()
    cursor.execute(query, (email_addr,))
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        raise Exception(f"No account found for email: {email_addr}")

    return row[0]  # returns acc_id for employee account

def get_or_create_chat(conn, acc_id):  ### NOT USED ANYMORE !!!

    cursor = conn.cursor()

    cursor.execute("""
        SELECT chat_id
        FROM chats
        WHERE acc_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (acc_id,))

    row = cursor.fetchone()

    if row:
        chat_id = row[0]
    else:
        cursor.execute("""
            INSERT INTO chats (acc_id)
            VALUES (%s)
        """, (acc_id,))

        conn.commit()
        chat_id = cursor.lastrowid

    cursor.close()
    return chat_id


def save_message(conn, chat_id, role, text):  # save the message written by user/chatbot to DB

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_messages (chat_id, sender_role, message_text)
        VALUES (%s, %s, %s)
    """, (chat_id, role, text,))

    cursor.execute("""
        UPDATE chats
        SET updated_at = NOW()
        WHERE chat_id = %s
    """, (chat_id,))

    conn.commit()
    cursor.close()


def load_chat_history(conn, chat_id, limit=10):  # get the latest messages from that chat
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sender_role, message_text
        FROM chat_messages
        WHERE chat_id = %s
        ORDER BY message_id DESC
        LIMIT %s
    """, (chat_id, limit))

    rows = cursor.fetchall()
    cursor.close()

    history = []
    current_user_message = None

    for role, text in rows:
        if role == "user":
            current_user_message = text
        elif role == "assistant" and current_user_message is not None:
            history.append((current_user_message, text))
            current_user_message = None

    return history[-limit:]


def create_new_chat(conn, acc_id, title="Yeni Sohbet"): # create new chat when user clicks create new chat button
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chats (acc_id, title)
        VALUES (%s, %s)
        """,
        (acc_id, title)
    )
    conn.commit()
    chat_id = cursor.lastrowid
    cursor.close()

    return chat_id


def get_user_chats_for_sidebar(conn, acc_id):  # to display the chats on UI sidebar

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT chat_id, title, updated_at
        FROM chats
        WHERE acc_id = %s
        ORDER BY updated_at DESC
    """, (acc_id,))

    chats = cursor.fetchall()

    cursor.close()

    return chats


def update_chat_title_from_first_message(conn, chat_id):  # update the chat title wrt first message
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT title
            FROM chats
            WHERE chat_id = %s
        """, (chat_id,))

        title_row = cursor.fetchone()

        if not title_row:
            return None

        current_title = title_row[0]

        if current_title and current_title.strip().lower() != "yeni sohbet":
            return current_title

        cursor.execute("""
            SELECT message_text
            FROM chat_messages
            WHERE chat_id = %s
            ORDER BY message_id ASC
            LIMIT 1
        """, (chat_id,))

        message_row = cursor.fetchone()

        if not message_row:
            return current_title

        first_message = message_row[0].strip()

        if not first_message:
            return current_title

        words = first_message.split()
        new_title = " ".join(words[:3])

        if not new_title:
            new_title = "Yeni sohbet"

        cursor.execute("""
            UPDATE chats
            SET title = %s
            WHERE chat_id = %s
        """, (new_title, chat_id))

        conn.commit()
        return new_title

    finally:
        cursor.close()

def get_chat_messages(conn, chat_id, acc_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT cm.message_id, cm.sender_role, cm.message_text, cm.created_at
    FROM chat_messages cm
    JOIN chats c ON cm.chat_id = c.chat_id
    WHERE cm.chat_id = %s AND c.acc_id = %s
    ORDER BY cm.message_id ASC
    """, (chat_id, acc_id))

    rows = cursor.fetchall()
    cursor.close()

    return rows


def rename_chat_title(conn, chat_id, acc_id, new_title):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE chats
            SET title = %s,
                updated_at = NOW()
            WHERE chat_id = %s AND acc_id = %s
        """, (new_title, chat_id, acc_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()


def chat_belongs_to_user(conn, chat_id, acc_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT 1
        FROM chats
        WHERE chat_id = %s AND acc_id = %s
        """, (chat_id, acc_id))
        row = cursor.fetchone()
        return row is not None
    finally:
        cursor.close()

def delete_chat(conn, chat_id, acc_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE cm
            FROM chat_messages cm
            JOIN chats c ON cm.chat_id = c.chat_id
            WHERE c.chat_id = %s AND c.acc_id = %s
        """, (chat_id, acc_id))

        cursor.execute("""
            DELETE FROM chats
            WHERE chat_id = %s AND acc_id = %s
        """, (chat_id, acc_id))

        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()


def get_name_from_email(conn, email):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT name, mail, user_type
            FROM users
            WHERE mail = %s
        """, (email,))
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()


def get_all_chatbot_categories(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT category_key, category_name, description, is_enabled, updated_at
            FROM chatbot_categories
            ORDER BY category_name ASC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()


def get_enabled_chatbot_categories(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT category_key, category_name, description
            FROM chatbot_categories
            WHERE is_enabled = TRUE
            ORDER BY category_name ASC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()


def is_category_enabled(conn, category_key: str) -> bool:
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT is_enabled
            FROM chatbot_categories
            WHERE category_key = %s
            """,
            (category_key,)
        )

        row = cursor.fetchone()

        # Kategori veritabanında yoksa kapalı kabul edilir.
        if row is None:
            return False

        value = row[0]

        # NULL değer kapalı kabul edilir.
        if value is None:
            return False

        # PostgreSQL BOOLEAN gibi gerçek boolean değerler.
        if isinstance(value, bool):
            return value

        # MySQL TINYINT veya integer değerler.
        if isinstance(value, int):
            return value == 1

        # String olarak dönen değerler.
        if isinstance(value, str):
            return value.strip().lower() in {
                "1",
                "true",
                "t",
                "yes",
                "on"
            }

        # Bilinmeyen veri tipi güvenli tarafta kapalı kabul edilir.
        return False

    finally:
        cursor.close()


def update_chatbot_category_status(conn, category_key, is_enabled):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE chatbot_categories
            SET is_enabled = %s
            WHERE category_key = %s
        """, (is_enabled, category_key))

        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()