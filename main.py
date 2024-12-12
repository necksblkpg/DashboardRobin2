from app import app, init_db
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    init_db()  # Initiera databasen, skapa tabeller och lägg in initial data om det behövs
    app.run(host="0.0.0.0", port=5000, debug=True)
