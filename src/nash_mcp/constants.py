import os
import sys
import uuid
import signal
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

# Use a file-based tracking system that persists between imports
# This ensures state is preserved even if modules are reloaded
def _get_pid_tracking_file():
    """Get the path to the PID tracking file for this session."""
    return NASH_SESSION_DIR / "tracked_pids.txt"

def add_pid(pid):
    """Add a PID to the global tracking set using a file-based approach."""
    pid = int(pid)  # Ensure it's an integer
    
    # Create a debug file to store the PID
    tracking_file = _get_pid_tracking_file()
    
    try:
        # Read existing PIDs
        pids = set()
        if tracking_file.exists():
            with open(tracking_file, 'r') as f:
                content = f.read().strip()
                if content:
                    pids = set(int(p) for p in content.split(',') if p.strip())
        
        # Add the new PID
        pids.add(pid)
        
        # Write back to file
        with open(tracking_file, 'w') as f:
            f.write(','.join(str(p) for p in pids))
            
        print(f"ADDED PID {pid} TO FILE TRACKER. Total PIDs: {len(pids)}")
        print(f"TRACKED PIDS: {','.join(str(p) for p in pids)}")
    except Exception as e:
        print(f"ERROR adding PID to tracker: {e}")
    
def remove_pid(pid):
    """Remove a PID from the global tracking set."""
    pid = int(pid)  # Ensure it's an integer
    tracking_file = _get_pid_tracking_file()
    
    try:
        # Read existing PIDs
        pids = set()
        if tracking_file.exists():
            with open(tracking_file, 'r') as f:
                content = f.read().strip()
                if content:
                    pids = set(int(p) for p in content.split(',') if p.strip())
        
        # Remove the PID
        if pid in pids:
            pids.remove(pid)
            
            # Write back to file
            with open(tracking_file, 'w') as f:
                f.write(','.join(str(p) for p in pids))
                
            print(f"REMOVED PID {pid} FROM FILE TRACKER. Total PIDs: {len(pids)}")
        else:
            print(f"PID {pid} not found in tracker")
    except Exception as e:
        print(f"ERROR removing PID from tracker: {e}")
    
def get_all_pids():
    """Return all tracked PIDs from the file."""
    tracking_file = _get_pid_tracking_file()
    
    try:
        if tracking_file.exists():
            with open(tracking_file, 'r') as f:
                content = f.read().strip()
                if content:
                    pids = [int(p) for p in content.split(',') if p.strip()]
                    print(f"READ {len(pids)} PIDS FROM TRACKER FILE: {','.join(str(p) for p in pids)}")
                    return pids
    except Exception as e:
        print(f"ERROR reading PIDs from tracker: {e}")
    
    return []
    
def clear_pids():
    """Clear all tracked PIDs."""
    tracking_file = _get_pid_tracking_file()
    
    try:
        # Write an empty file
        with open(tracking_file, 'w') as f:
            f.write('')
        print("CLEARED ALL PIDS FROM TRACKER")
    except Exception as e:
        print(f"ERROR clearing PIDs: {e}")
    
def kill_all_pids():
    """Attempt to kill all tracked processes with SIGTERM."""
    pids = get_all_pids()
    print(f"KILLING {len(pids)} PIDS WITH SIGTERM: {','.join(str(p) for p in pids)}")
    
    for pid in pids:
        try:
            # Try SIGTERM first
            os.kill(pid, signal.SIGTERM)
            print(f"SENT SIGTERM TO PID {pid}")
            # Keep track that we attempted to kill this PID
            # Don't remove from tracking yet - we'll verify later
        except ProcessLookupError:
            # Process doesn't exist anymore, remove from tracking
            remove_pid(pid)
            print(f"PID {pid} no longer exists, removed from tracking")
        except Exception as e:
            # Other errors, just continue
            print(f"ERROR sending SIGTERM to PID {pid}: {e}")
            
def kill_all_pids_forcefully():
    """Force kill any remaining tracked processes with SIGKILL."""
    pids = get_all_pids()
    print(f"FORCEFULLY KILLING {len(pids)} PIDS WITH SIGKILL: {','.join(str(p) for p in pids)}")
    
    for pid in pids:
        try:
            # Force kill with SIGKILL
            os.kill(pid, signal.SIGKILL)
            print(f"SENT SIGKILL TO PID {pid}")
            # Only remove if it's confirmed gone
            try:
                os.kill(pid, 0)  # Check if process still exists
                print(f"WARNING: PID {pid} still exists after SIGKILL")
            except ProcessLookupError:
                remove_pid(pid)
                print(f"PID {pid} successfully killed and removed from tracking")
        except ProcessLookupError:
            # Process doesn't exist anymore
            remove_pid(pid)
            print(f"PID {pid} no longer exists, removed from tracking")
        except Exception as e:
            # Other errors, just continue
            print(f"ERROR sending SIGKILL to PID {pid}: {e}")
