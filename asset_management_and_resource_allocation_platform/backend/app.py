from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from auth import clear_session_cookie, hash_password, make_session, read_session, session_cookie, verify_password
from database import ROOT_DIR, connect, initialize_database, one_to_dict, rows_to_dicts


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))
FRONTEND_DIR = ROOT_DIR / "frontend"


class AppError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


class AssetManagerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def do_PUT(self):
        self.handle_request()

    def do_DELETE(self):
        self.handle_request()

    def handle_request(self):
        try:
            initialize_overdue_bookings()
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                self.route_api(parsed)
            else:
                self.serve_frontend(parsed.path)
        except AppError as error:
            self.send_json({"error": error.message}, error.status)
        except Exception as error:
            self.send_json({"error": str(error)}, 500)

    def route_api(self, parsed):
        method = self.command
        path = parsed.path
        query = parse_qs(parsed.query)

        if method == "POST" and path == "/api/register":
            return self.register()
        if method == "POST" and path == "/api/login":
            return self.login()
        if method == "POST" and path == "/api/logout":
            return self.logout()
        if method == "GET" and path == "/api/me":
            return self.send_json({"user": self.current_user()})
        if method == "GET" and path == "/api/assets":
            return self.list_assets(query)
        if method == "POST" and path == "/api/assets":
            return self.save_asset()
        if method == "PUT" and path.startswith("/api/assets/"):
            return self.save_asset(asset_id=int(path.rsplit("/", 1)[1]))
        if method == "DELETE" and path.startswith("/api/assets/"):
            return self.delete_asset(int(path.rsplit("/", 1)[1]))
        if method == "GET" and path == "/api/bookings":
            return self.list_bookings()
        if method == "POST" and path == "/api/bookings":
            return self.create_booking()
        if method == "POST" and path.startswith("/api/bookings/"):
            booking_id, action = parse_booking_action(path)
            return self.update_booking_status(booking_id, action)
        if method == "GET" and path == "/api/analytics":
            return self.analytics()

        raise AppError(404, "API route not found")

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode())
        except json.JSONDecodeError:
            raise AppError(400, "Request body must be valid JSON")

    def current_user(self):
        session = read_session(self.headers)
        if not session:
            raise AppError(401, "Please log in first")
        return session

    def require_admin(self):
        user = self.current_user()
        if user["role"] != "admin":
            raise AppError(403, "Admin access is required")
        return user

    def register(self):
        data = self.read_json()
        name = clean_text(data.get("name"))
        email = clean_text(data.get("email")).lower()
        password = data.get("password", "")
        if not name or not email or len(password) < 6:
            raise AppError(400, "Name, email and a 6 character password are required")

        with connect() as db:
            try:
                cursor = db.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'user')",
                    (name, email, hash_password(password)),
                )
            except Exception:
                raise AppError(409, "An account with this email already exists")
            user = db.execute("SELECT id, name, email, role FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()

        token = make_session(user)
        self.send_json({"user": dict(user)}, headers={"Set-Cookie": session_cookie(token)})

    def login(self):
        data = self.read_json()
        email = clean_text(data.get("email")).lower()
        password = data.get("password", "")
        with connect() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not verify_password(password, user["password_hash"]):
            raise AppError(401, "Invalid email or password")
        token = make_session(user)
        public_user = {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
        self.send_json({"user": public_user}, headers={"Set-Cookie": session_cookie(token)})

    def logout(self):
        self.send_json({"message": "Logged out"}, headers={"Set-Cookie": clear_session_cookie()})

    def list_assets(self, query):
        self.current_user()
        search = f"%{query.get('search', [''])[0].strip()}%"
        category = query.get("category", [""])[0].strip()
        sql = """
            SELECT assets.*,
                assets.quantity_total - COALESCE((
                    SELECT SUM(quantity_requested)
                    FROM bookings
                    WHERE bookings.asset_id = assets.id
                      AND bookings.status IN ('approved', 'issued', 'overdue')
                      AND date('now') BETWEEN bookings.start_date AND bookings.end_date
                ), 0) AS available_now
            FROM assets
            WHERE (asset_name LIKE ? OR description LIKE ?)
        """
        params = [search, search]
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY category, asset_name"
        with connect() as db:
            assets = rows_to_dicts(db.execute(sql, params).fetchall())
            categories = [row["category"] for row in db.execute("SELECT DISTINCT category FROM assets ORDER BY category")]
        self.send_json({"assets": assets, "categories": categories})

    def save_asset(self, asset_id=None):
        self.require_admin()
        data = self.read_json()
        asset_name = clean_text(data.get("asset_name"))
        category = clean_text(data.get("category"))
        description = clean_text(data.get("description"))
        quantity_total = int(data.get("quantity_total", 0))
        status = clean_text(data.get("status")) or "Available"
        if not asset_name or not category or quantity_total < 0:
            raise AppError(400, "Asset name, category and quantity are required")

        with connect() as db:
            if asset_id:
                db.execute(
                    """
                    UPDATE assets
                    SET asset_name = ?, category = ?, description = ?, quantity_total = ?, status = ?
                    WHERE id = ?
                    """,
                    (asset_name, category, description, quantity_total, status, asset_id),
                )
            else:
                db.execute(
                    """
                    INSERT INTO assets (asset_name, category, description, quantity_total, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (asset_name, category, description, quantity_total, status),
                )
        self.send_json({"message": "Asset saved"})

    def delete_asset(self, asset_id):
        self.require_admin()
        with connect() as db:
            active_count = db.execute(
                "SELECT COUNT(*) AS count FROM bookings WHERE asset_id = ? AND status IN ('pending', 'approved', 'issued', 'overdue')",
                (asset_id,),
            ).fetchone()["count"]
            if active_count:
                raise AppError(409, "This asset has active booking records")
            db.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        self.send_json({"message": "Asset deleted"})

    def list_bookings(self):
        user = self.current_user()
        sql = """
            SELECT bookings.*, assets.asset_name, assets.category, users.name AS user_name
            FROM bookings
            JOIN assets ON bookings.asset_id = assets.id
            JOIN users ON bookings.user_id = users.id
        """
        params = []
        if user["role"] != "admin":
            sql += " WHERE bookings.user_id = ?"
            params.append(user["id"])
        sql += " ORDER BY bookings.created_at DESC"
        with connect() as db:
            bookings = rows_to_dicts(db.execute(sql, params).fetchall())
        self.send_json({"bookings": bookings})

    def create_booking(self):
        user = self.current_user()
        data = self.read_json()
        asset_id = int(data.get("asset_id", 0))
        quantity = int(data.get("quantity_requested", 0))
        start_date = clean_text(data.get("start_date"))
        end_date = clean_text(data.get("end_date"))
        purpose = clean_text(data.get("purpose"))

        if quantity <= 0 or not start_date or not end_date or start_date > end_date:
            raise AppError(400, "Choose a valid quantity and date range")

        available = available_for_range(asset_id, start_date, end_date)
        if quantity > available:
            raise AppError(409, f"Only {available} units are available for those dates")

        with connect() as db:
            db.execute(
                """
                INSERT INTO bookings (asset_id, user_id, quantity_requested, start_date, end_date, purpose, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """,
                (asset_id, user["id"], quantity, start_date, end_date, purpose),
            )
        self.send_json({"message": "Booking request submitted"})

    def update_booking_status(self, booking_id, action):
        self.require_admin()
        allowed = {"approve": "approved", "reject": "rejected", "issue": "issued", "return": "returned"}
        if action not in allowed:
            raise AppError(404, "Unknown booking action")
        new_status = allowed[action]
        returned_at_sql = ", returned_at = date('now')" if new_status == "returned" else ""

        with connect() as db:
            booking = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
            if not booking:
                raise AppError(404, "Booking not found")
            if new_status in ("approved", "issued"):
                available = available_for_range(booking["asset_id"], booking["start_date"], booking["end_date"], booking_id)
                if booking["quantity_requested"] > available:
                    raise AppError(409, "Inventory is no longer available for this booking")
            db.execute(f"UPDATE bookings SET status = ? {returned_at_sql} WHERE id = ?", (new_status, booking_id))
        self.send_json({"message": f"Booking marked as {new_status}"})

    def analytics(self):
        self.current_user()
        with connect() as db:
            summary = one_to_dict(db.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM assets) AS total_assets,
                    (SELECT COALESCE(SUM(quantity_total), 0) FROM assets) AS total_units,
                    (SELECT COUNT(*) FROM bookings WHERE status IN ('approved', 'issued')) AS active_bookings,
                    (SELECT COUNT(*) FROM bookings WHERE status = 'overdue') AS overdue_returns,
                    (SELECT COUNT(*) FROM bookings WHERE status = 'pending') AS pending_requests
                """
            ).fetchone())
            utilization = rows_to_dicts(db.execute(
                """
                SELECT assets.asset_name, COUNT(bookings.id) AS booking_count,
                       COALESCE(SUM(bookings.quantity_requested), 0) AS units_booked
                FROM assets
                LEFT JOIN bookings ON bookings.asset_id = assets.id
                GROUP BY assets.id
                ORDER BY units_booked DESC, booking_count DESC
                LIMIT 8
                """
            ).fetchall())
            status_mix = rows_to_dicts(db.execute(
                "SELECT status, COUNT(*) AS count FROM bookings GROUP BY status ORDER BY count DESC"
            ).fetchall())
        self.send_json({"summary": summary, "utilization": utilization, "status_mix": status_mix})

    def serve_frontend(self, request_path):
        file_path = FRONTEND_DIR / (request_path.lstrip("/") or "index.html")
        if not file_path.exists() or file_path.is_dir():
            file_path = FRONTEND_DIR / "index.html"
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def send_json(self, data, status=200, headers=None):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def clean_text(value):
    return str(value or "").strip()


def parse_booking_action(path):
    parts = path.strip("/").split("/")
    if len(parts) != 4:
        raise AppError(404, "Booking route not found")
    return int(parts[2]), parts[3]


def available_for_range(asset_id, start_date, end_date, ignore_booking_id=None):
    with connect() as db:
        asset = db.execute("SELECT quantity_total FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            raise AppError(404, "Asset not found")
        params = [asset_id, start_date, end_date]
        ignore_clause = ""
        if ignore_booking_id:
            ignore_clause = "AND id != ?"
            params.append(ignore_booking_id)
        used = db.execute(
            f"""
            SELECT COALESCE(SUM(quantity_requested), 0) AS used
            FROM bookings
            WHERE asset_id = ?
              AND status IN ('approved', 'issued', 'overdue')
              AND start_date <= ?
              AND end_date >= ?
              {ignore_clause}
            """,
            params,
        ).fetchone()["used"]
    return max(0, asset["quantity_total"] - used)


def initialize_overdue_bookings():
    with connect() as db:
        db.execute(
            "UPDATE bookings SET status = 'overdue' WHERE status = 'issued' AND end_date < ?",
            (date.today().isoformat(),),
        )


def run():
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), AssetManagerHandler)
    print(f"Asset Management Platform running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
