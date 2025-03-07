import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for required environment variables
required_vars = ["NASH_BASE_PATH", "NASH_SECRETS_PATH", "NASH_TASKS_PATH", "NASH_LOGS_PATH"]
missing_vars = [var for var in required_vars if var not in os.environ]

if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    print("Please create a .env file with all required variables.", file=sys.stderr)
    sys.exit(1)

# Get paths from environment variables with no defaults
MAC_BASE_PATH = Path(os.environ["NASH_BASE_PATH"])
MAC_SECRETS_PATH = Path(os.environ["NASH_SECRETS_PATH"])
MAC_TASKS_PATH = Path(os.environ["NASH_TASKS_PATH"])
MAC_LOGS_PATH = Path(os.environ["NASH_LOGS_PATH"])
