import os
import mysql.connector

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# MYSQL CONNECTION
# ============================================================

def get_connection():

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    username,
    password,
    role="STAFF"
):

    username = str(username).strip()
    password = str(password)

    role = str(role).strip().upper()

    if not username:

        return {
            "success": False,
            "message": "Username is required."
        }

    if not password:

        return {
            "success": False,
            "message": "Password is required."
        }

    if role not in ["ADMIN", "STAFF"]:

        return {
            "success": False,
            "message":
                "Role must be ADMIN or STAFF."
        }

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # CHECK EXISTING USER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            return {
                "success": False,
                "message":
                    "Username already exists."
            }

        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        password_hash = (
            generate_password_hash(password)
        )

        # ----------------------------------------------------
        # INSERT USER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password_hash,
                role
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                username,
                password_hash,
                role
            )
        )

        user_id = cursor.lastrowid

        connection.commit()

        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "role": role,
            "message":
                "User created successfully."
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# LOGIN
# ============================================================

def authenticate_user(
    username,
    password
):

    username = str(username).strip()
    password = str(password)

    if not username or not password:

        return {
            "success": False,
            "message":
                "Username and password are required."
        }

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                user_id,
                username,
                password_hash,
                role

            FROM users

            WHERE username = %s

            LIMIT 1
            """,
            (username,)
        )

        user = cursor.fetchone()

        if not user:

            return {
                "success": False,
                "message":
                    "Invalid username or password."
            }

        password_valid = (
            check_password_hash(
                user["password_hash"],
                password
            )
        )

        if not password_valid:

            return {
                "success": False,
                "message":
                    "Invalid username or password."
            }

        return {
            "success": True,
            "user_id":
                user["user_id"],
            "username":
                user["username"],
            "role":
                user["role"],
            "message":
                "Login successful."
        }

    except Exception as e:

        return {
            "success": False,
            "message":
                str(e)
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET ALL USERS
# ============================================================

def get_all_users():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                user_id,
                username,
                role,
                created_at

            FROM users

            ORDER BY
                user_id
            """
        )

        return cursor.fetchall()

    finally:

        cursor.close()
        connection.close()


# ============================================================
# DELETE USER
# ============================================================

def delete_user(
    user_id
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM users

            WHERE user_id = %s
            """,
            (user_id,)
        )

        if cursor.rowcount == 0:

            return {
                "success": False,
                "message":
                    "User not found."
            }

        connection.commit()

        return {
            "success": True,
            "message":
                "User deleted successfully."
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("           SHOP SENSE AUTH TEST")
    print("=" * 60)

    result = create_user(
        "admin",
        "admin123",
        "ADMIN"
    )

    print("\nCREATE USER")
    print(result)

    print("\nLOGIN TEST")

    login = authenticate_user(
        "admin",
        "admin123"
    )

    print(login)

    print("\nUSERS")

    try:

        users = get_all_users()

        for user in users:

            print({
                "user_id":
                    user["user_id"],

                "username":
                    user["username"],

                "role":
                    user["role"],

                "created_at":
                    str(
                        user["created_at"]
                    )
            })

    except Exception as e:

        print(
            "User listing error:",
            e
        )

    print("\n" + "=" * 60)