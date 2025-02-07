import sqlite3
from datetime import datetime

# Step 1: Set up SQLite database to store build history
def create_database():
    """Create the database and the 'builds' table if it doesn't exist."""
    print("Creating database and table if not exists.")  # Debugging output
    try:
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
        print("Database created and table initialized.")
    except Exception as e:
        print(f"Error during database creation: {e}")

# Step 2: Log the build information
def log_build(commit_id, build_logs):
    """Log the build details to the database."""
    try:
        print(f"Logging build for commit: {commit_id}")  # Debugging output
        conn = sqlite3.connect('build_history.db')
        cursor = conn.cursor()
        build_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp
        cursor.execute('''
            INSERT INTO builds (commit_id, build_date, build_logs)
            VALUES (?, ?, ?)
        ''', (commit_id, build_date, build_logs))
        conn.commit()
        conn.close()
        print(f"Build logged: {commit_id} on {build_date}")
    except Exception as e:
        print(f"Error logging build: {e}")

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
        print(f"Cloning {repo_url} branch {branch} to {temp_dir}")  # Debugging output
        repo = Repo.clone_from(repo_url, temp_dir, branch=branch)
        commit_id = repo.head.commit.hexsha  # Get commit ID
        return commit_id, temp_dir
    except Exception as e:
        print(f"Error during clone: {e}")
        return None, None
    finally:
        shutil.rmtree(temp_dir)
