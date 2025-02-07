import sqlite3
from datetime import datetime

# Step 1: Set up SQLite database to store build history
def create_database():
    """Create the database and the 'builds' table if it doesn't exist."""
    conn = sqlite3.connect('build_history.db')  # Database file
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS builds (
            id INTEGER PRIMARY KEY,
            commit_id TEXT,
            build_date TEXT,
            build_logs TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Step 2: Log the build information
def log_build(commit_id, build_logs):
    """Log the build details to the database."""
    conn = sqlite3.connect('build_history.db')
    cursor = conn.cursor()
    build_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp
    cursor.execute('''
        INSERT INTO builds (commit_id, build_date, build_logs)
        VALUES (?, ?, ?)
    ''', (commit_id, build_date, build_logs))
    conn.commit()
    conn.close()

# Step 3: Generate a unique URL for each build
def get_build_url(commit_id):
    """Generate a unique URL for a specific build."""
    return f"http://localhost:8008/build/{commit_id}"

# Step 4: Clone the repository and check out the branch
def clone_check(repo_url, branch):
    """Clone the repository and perform syntax checking."""
    import tempfile
    import shutil
    from git import Repo
    temp_dir = tempfile.mkdtemp()
    try:
        repo = Repo.clone_from(repo_url, temp_dir, branch=branch)
        commit_id = repo.head.commit.hexsha  # Get commit ID
        return commit_id, temp_dir
    except Exception as e:
        return None, None
    finally:
        shutil.rmtree(temp_dir)
