import os
import datetime
from functools import wraps

import jwt
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Allow the React dev server to call this API. Update the origin if you
# deploy the frontend somewhere else or run it on a different port.
CORS(app, resources={r"/api/*": {"origins": os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")}})

SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")
TOKEN_EXP_HOURS = 24


# Database configuration
# Set these via environment variables in production instead of hardcoding.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "auth_app"),
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)



# JWT helpers


def generate_token(user_id, username):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXP_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def login_required(view_func):
    """Decorator that validates the Authorization: Bearer <token> header."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        request.user_id = payload["user_id"]
        request.username = payload["username"]
        return view_func(*args, **kwargs)

    return wrapped_view



# Auth routes


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not username or not email or not password:
        return jsonify({"error": "All fields are required."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    hashed_password = generate_password_hash(password)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email),
        )
        if cursor.fetchone():
            return jsonify({"error": "Username or email already registered."}), 409

        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, hashed_password),
        )
        conn.commit()
        cursor.close()
        return jsonify({"message": "Registration successful. Please log in."}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn is not None:
            conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s OR email = %s",
            (username, username),
        )
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user["password_hash"], password):
            token = generate_token(user["id"], user["username"])
            return jsonify({
                "token": token,
                "user": {"id": user["id"], "username": user["username"]},
            }), 200

        return jsonify({"error": "Invalid username/email or password."}), 401

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn is not None:
            conn.close()


@app.route("/api/me", methods=["GET"])
@login_required
def me():
    return jsonify({"id": request.user_id, "username": request.username}), 200



# Blog routes


@app.route("/api/blogs", methods=["GET"])
@login_required
def blog_list():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, content, created_at, updated_at FROM blogs "
            "WHERE user_id = %s ORDER BY created_at DESC",
            (request.user_id,),
        )
        blogs = cursor.fetchall()
        cursor.close()
        for blog in blogs:
            blog["created_at"] = blog["created_at"].isoformat()
            blog["updated_at"] = blog["updated_at"].isoformat()
        return jsonify(blogs), 200
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn is not None:
            conn.close()


@app.route("/api/blogs", methods=["POST"])
@login_required
def blog_create():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title or not content:
        return jsonify({"error": "Title and content are required."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO blogs (user_id, title, content) VALUES (%s, %s, %s)",
            (request.user_id, title, content),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return jsonify({"id": new_id, "message": "Blog post created."}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn is not None:
            conn.close()


@app.route("/api/blogs/<int:blog_id>", methods=["GET"])
@login_required
def blog_view(blog_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, content, created_at, updated_at FROM blogs "
            "WHERE id = %s AND user_id = %s",
            (blog_id, request.user_id),
        )
        blog = cursor.fetchone()
        cursor.close()

        if blog is None:
            return jsonify({"error": "Blog post not found."}), 404

        blog["created_at"] = blog["created_at"].isoformat()
        blog["updated_at"] = blog["updated_at"].isoformat()
        return jsonify(blog), 200
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn is not None:
            conn.close()


@app.route("/api/blogs/<int:blog_id>", methods=["PUT"])
@login_required
def blog_update(blog_id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title or not content:
        return jsonify({"error": "Title and content are required."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE blogs SET title = %s, content = %s WHERE id = %s AND user_id = %s",
            (title, content, blog_id, request.user_id),
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()

        if affected == 0:
            return jsonify({"error": "Blog post not found."}), 404

        return jsonify({"message": "Blog post updated."}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn is not None:
            conn.close()


@app.route("/api/blogs/<int:blog_id>", methods=["DELETE"])
@login_required
def blog_delete(blog_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM blogs WHERE id = %s AND user_id = %s",
            (blog_id, request.user_id),
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()

        if affected == 0:
            return jsonify({"error": "Blog post not found."}), 404

        return jsonify({"message": "Blog post deleted."}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
