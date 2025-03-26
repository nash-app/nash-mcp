import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for required environment variables
required_vars = ["NASH_SECRETS_PATH", "NASH_TASKS_PATH", "NASH_LOGS_PATH", "NASH_SESSIONS_PATH"]
missing_vars = [var for var in required_vars if var not in os.environ]

if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    print("Please create a .env file with all required variables.", file=sys.stderr)
    sys.exit(1)

# Get paths from environment variables with no defaults
MAC_SECRETS_PATH = Path(os.environ["NASH_SECRETS_PATH"])
MAC_TASKS_PATH = Path(os.environ["NASH_TASKS_PATH"])
MAC_LOGS_PATH = Path(os.environ["NASH_LOGS_PATH"])
MAC_SESSIONS_PATH = Path(os.environ["NASH_SESSIONS_PATH"])

# Generate a unique session ID with timestamp
NASH_SESSION_ID = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
NASH_SESSION_DIR = MAC_SESSIONS_PATH / NASH_SESSION_ID
