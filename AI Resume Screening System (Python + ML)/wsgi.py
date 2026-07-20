from app import app, init_db

# Initialize database schema and pre-loaded models on startup
init_db()

if __name__ == '__main__':
    app.run()
