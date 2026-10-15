import hashlib
import hmac
import os

import mysql.connector
from mysql.connector import Error


HASH_PREFIX = "pbkdf2"
HASH_ITERATIONS = 200_000


def hash_password(password):
    salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS
    )

    return f"{HASH_PREFIX}${salt.hex()}${digest.hex()}"


def is_hashed(stored):
    return isinstance(stored, str) and stored.startswith(HASH_PREFIX + "$")


def verify_password(password, stored):
    if not is_hashed(stored):
        return False

    try:
        _, salt_hex, hash_hex = stored.split("$")

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            HASH_ITERATIONS
        )

        return hmac.compare_digest(digest.hex(), hash_hex)

    except (ValueError, TypeError):
        return False


def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            database="caberte_space_invaders_db",
            user="root",
            password=""
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print(f"Database Connection Error: {e}")

    return None


def setup_database():
    conn = create_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("SHOW TABLES LIKE 'players'")
        players_exists = cursor.fetchone()

        if not players_exists:
            cursor.execute("""
                CREATE TABLE players (
                    player_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        cursor.execute("SHOW TABLES LIKE 'scores'")
        scores_exists = cursor.fetchone()

        if not scores_exists:
            cursor.execute("""
                CREATE TABLE scores (
                    score_id INT AUTO_INCREMENT PRIMARY KEY,
                    player_id INT NOT NULL,
                    score INT NOT NULL DEFAULT 0,
                    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    level INT NOT NULL DEFAULT 1,
                    FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
                    ON DELETE CASCADE
                )
            """)
        else:
            cursor.execute("SHOW COLUMNS FROM scores")
            score_columns = [row[0] for row in cursor.fetchall()]

            if "date_added" not in score_columns:
                cursor.execute("""
                    ALTER TABLE scores
                    ADD COLUMN date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                """)

            if "level" not in score_columns:
                cursor.execute("""
                    ALTER TABLE scores
                    ADD COLUMN level INT NOT NULL DEFAULT 1
                """)

        conn.commit()
        return True

    except Error as e:
        print(f"Database Setup Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def get_db_connection():
    return create_connection()


def register_player(username, password):
    conn = get_db_connection()

    if not conn:
        return False, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT player_id
            FROM players
            WHERE username = %s
            """,
            (username,)
        )

        if cursor.fetchone():
            return False, "USERNAME ALREADY EXISTS"

        cursor.execute(
            """
            INSERT INTO players
            (username, password)
            VALUES (%s, %s)
            """,
            (username, hash_password(password))
        )

        conn.commit()

        return True, "ACCOUNT CREATED"

    except Error as e:
        conn.rollback()
        print(f"Registration Error: {e}")
        return False, f"DATABASE ERROR: {e}"

    finally:
        cursor.close()
        conn.close()


def login_player(username, password):
    conn = get_db_connection()

    if not conn:
        print("Login Error: Database connection failed")
        return None

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                player_id,
                username,
                password
            FROM players
            WHERE username = %s
            """,
            (username,)
        )

        player = cursor.fetchone()

        if not player:
            return None

        stored = player["password"]

        if is_hashed(stored):
            if not verify_password(password, stored):
                return None

        else:
            if stored != password:
                return None

            cursor.execute(
                """
                UPDATE players
                SET password = %s
                WHERE player_id = %s
                """,
                (hash_password(password), player["player_id"])
            )

            conn.commit()

        player.pop("password", None)

        return player

    except Error as e:
        print(f"Login Error: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def save_score(player_id, score, level=1):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO scores
            (player_id, score, level, date_added)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (player_id, score, level)
        )

        conn.commit()

        return True

    except Error as e:
        print(f"Score Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def load_leaderboard(limit=100, period="all"):
    """Every saved score (not only each player's best), highest first.
    period: "all" | "weekly" (last 7 days) | "daily" (last 24 hours)"""
    conn = get_db_connection()

    if not conn:
        return []

    where = ""

    if period == "weekly":
        where = "WHERE s.date_added >= (NOW() - INTERVAL 7 DAY)"
    elif period == "daily":
        where = "WHERE s.date_added >= (NOW() - INTERVAL 1 DAY)"

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
            SELECT
                p.player_id,
                p.username,
                s.score,
                s.level,
                s.date_added
            FROM scores s
            INNER JOIN players p
                ON p.player_id = s.player_id
            {where}
            ORDER BY s.score DESC,
                     s.date_added DESC
            LIMIT %s
            """,
            (limit,)
        )

        return cursor.fetchall()

    except Error as e:
        print(f"Leaderboard Error: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


def get_player_stats(player_id):
    """Numbers for the profile screen."""
    stats = {
        "highest_score": 0,
        "total_games": 0,
        "total_score": 0,
        "best_level": 0,
    }

    conn = get_db_connection()

    if not conn:
        return stats

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                COALESCE(MAX(score), 0),
                COUNT(*),
                COALESCE(SUM(score), 0),
                COALESCE(MAX(level), 0)
            FROM scores
            WHERE player_id = %s
            """,
            (player_id,)
        )

        row = cursor.fetchone()

        if row:
            stats["highest_score"] = int(row[0])
            stats["total_games"] = int(row[1])
            stats["total_score"] = int(row[2])
            stats["best_level"] = int(row[3])

        return stats

    except Error as e:
        print(f"Stats Error: {e}")
        return stats

    finally:
        cursor.close()
        conn.close()


def get_player_highest_score(player_id):
    conn = get_db_connection()

    if not conn:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(MAX(score), 0)
            FROM scores
            WHERE player_id = %s
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

        return 0

    except Error as e:
        print(f"Highest Score Error: {e}")
        return 0

    finally:
        cursor.close()
        conn.close()


def update_player_profile(player_id, new_username):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT player_id
            FROM players
            WHERE username = %s
            AND player_id != %s
            """,
            (new_username, player_id)
        )

        if cursor.fetchone():
            return False

        cursor.execute(
            """
            UPDATE players
            SET username = %s
            WHERE player_id = %s
            """,
            (new_username, player_id)
        )

        conn.commit()

        return True

    except Error as e:
        print(f"Profile Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def delete_player(player_id):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM players
            WHERE player_id = %s
            """,
            (player_id,)
        )

        conn.commit()

        return True

    except Error as e:
        print(f"Delete Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    if setup_database():
        print("DATABASE READY")
    else:
        print("DATABASE SETUP FAILED")