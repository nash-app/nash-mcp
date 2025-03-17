import sys
import logging
import traceback
import os
import signal
import psutil
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from mcp.server.fastmcp import FastMCP

# Nash imports
from nash_mcp.constants import MAC_LOGS_PATH, NASH_SESSION_DIR, NASH_SESSION_ID, MAC_SESSIONS_PATH

# Execute
from nash_mcp.execute import execute_command, execute_python, list_installed_packages, get_file_content, edit_python_file, list_session_files
from nash_mcp.execute.execute_python import active_python_processes
from nash_mcp.execute.execute_command import active_processes

# Fetch
from nash_mcp.fetch_webpage import fetch_webpage

# Web Automation
from nash_mcp.operate_browser import operate_browser

# Secrets
from nash_mcp.nash_secrets import nash_secrets

# Tasks
from nash_mcp.nash_tasks import (
    save_nash_task, list_nash_tasks, run_nash_task, delete_nash_task,
    execute_task_script, view_task_details
)


def setup_logging():
    """Configure logging for the Nash MCP server."""
    try:
        # Create logs directory if it doesn't exist
        MAC_LOGS_PATH.mkdir(parents=True, exist_ok=True)
        
        # Create a timestamped log file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = MAC_LOGS_PATH / f"nash_mcp_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stderr)
            ]
        )
        
        logging.info(f"Logging initialized. Log file: {log_file}")
        return True
    except Exception as e:
        print(f"Error setting up logging: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return False


def kill_process_tree(pid):
    """Kill a process and all its children using psutil with extra force."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Log all processes we're about to kill
        logging.info(f"Preparing to kill process tree for PID {pid} with {len(children)} children")
        for child in children:
            try:
                cmdline = " ".join(child.cmdline()) if child.cmdline() else "unknown"
                logging.info(f"Child process to kill: {child.pid} ({child.name()}) - cmdline: {cmdline}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                logging.info(f"Child process to kill: {child.pid} (info not available)")
        
        # Kill children first
        for child in children:
            try:
                # Try SIGTERM first
                child.terminate()
                logging.info(f"Sent SIGTERM to child process {child.pid}")
            except psutil.NoSuchProcess:
                logging.warning(f"Child process {child.pid} already gone")
            except Exception as e:
                logging.error(f"Error terminating child {child.pid}: {e}")
        
        # Give processes time to terminate gracefully
        gone, still_alive = psutil.wait_procs(children, timeout=1)
        
        # Kill any remaining children forcefully with SIGKILL
        for child in still_alive:
            try:
                child.kill()
                logging.info(f"Sent SIGKILL to child process {child.pid}")
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                logging.error(f"Error killing child {child.pid}: {e}")
        
        # Double-check for any remaining children that might have been missed
        try:
            remaining_children = parent.children(recursive=True)
            if remaining_children:
                logging.warning(f"Found {len(remaining_children)} children still alive after first kill attempt")
                for child in remaining_children:
                    try:
                        os.kill(child.pid, signal.SIGKILL)
                        logging.info(f"Forcefully killed remaining child {child.pid} with os.kill SIGKILL")
                    except Exception as e:
                        logging.error(f"Failed to kill remaining child {child.pid}: {e}")
        except Exception as e:
            logging.error(f"Error checking for remaining children: {e}")
                
        # Terminate parent
        if parent.is_running():
            parent.terminate()
            logging.info(f"Sent SIGTERM to parent process {pid}")
            
            # Give parent time to terminate
            try:
                parent.wait(timeout=1)
            except psutil.TimeoutExpired:
                # Kill parent forcefully
                if parent.is_running():
                    parent.kill()
                    logging.info(f"Sent SIGKILL to parent process {pid}")
                    
                    # Final check
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        # This is expected if the process is already gone
                        pass
        
        # Final verification
        try:
            if psutil.pid_exists(pid):
                logging.warning(f"Process {pid} still exists after kill attempts!")
                os.kill(pid, signal.SIGKILL)
                logging.info(f"Sent final SIGKILL to process {pid}")
        except Exception as e:
            logging.error(f"Error during final kill verification: {e}")
    
    except psutil.NoSuchProcess:
        logging.warning(f"Process {pid} not found")
    except Exception as e:
        logging.error(f"Error killing process tree for {pid}: {e}")


def kill_all_python_processes():
    """Find and kill all Python processes that match our interpreter."""
    our_python = sys.executable
    our_pid = os.getpid()
    
    try:
        logging.info(f"Scanning for Python processes using our interpreter: {our_python}")
        logging.info(f"Our server PID to exclude: {our_pid}")
        
        # Get all running Python processes first and log them
        python_processes = []
        logging.info("Listing ALL Python processes currently running:")
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else "unknown"
                    exe = proc.info['exe'] if proc.info['exe'] else "unknown"
                    pid = proc.info['pid']
                    parent_pid = proc.ppid() if hasattr(proc, 'ppid') else "unknown"
                    
                    try:
                        # Try to get the parent process name
                        parent_name = "unknown"
                        if parent_pid != "unknown":
                            try:
                                parent = psutil.Process(parent_pid)
                                parent_name = parent.name()
                            except:
                                pass
                    except:
                        parent_name = "unknown"
                    
                    logging.info(f"Python process found: PID={pid}, EXE={exe}, PPID={parent_pid} (parent={parent_name}), CMDLINE={cmdline}")
                    
                    # Check if it's a process we should kill
                    if exe == our_python and pid != our_pid:
                        python_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
                logging.warning(f"Error inspecting process: {e}")
                continue
        
        # Log the specific processes we're going to kill
        if python_processes:
            logging.info(f"Found {len(python_processes)} Python processes to kill")
            for proc in python_processes:
                try:
                    cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else "unknown"
                    pid = proc.info['pid']
                    logging.info(f"Will kill Python process: PID={pid}, CMDLINE={cmdline}")
                    
                    # Check if this appears to be our sleep process
                    if "sleep" in cmdline.lower():
                        logging.info(f"FOUND SLEEP PROCESS TO KILL: PID={pid}, CMDLINE={cmdline}")
                    
                    # Kill the process tree
                    kill_process_tree(pid)
                    
                    # Verify it's gone
                    if psutil.pid_exists(pid):
                        logging.warning(f"Process {pid} STILL EXISTS after kill attempt!")
                        # Try direct kill as last resort
                        try:
                            os.kill(pid, signal.SIGKILL)
                            logging.info(f"Sent direct SIGKILL to {pid}")
                        except:
                            pass
                    else:
                        logging.info(f"Successfully killed process {pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    logging.error(f"Error killing Python process {proc.info['pid']}: {e}")
        else:
            logging.info("No matching Python processes found to kill")
    except Exception as e:
        logging.error(f"Error in kill_all_python_processes: {e}")


@asynccontextmanager
async def nash_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """
    Manage application lifecycle and process cleanup.
    
    This context manager ensures all child processes are properly cleaned up
    when the server shuts down, regardless of how termination occurs.
    """
    context = {
        "server_pid": os.getpid(),
        "active_python_processes": active_python_processes,
        "active_shell_processes": active_processes
    }
    
    logging.info(f"Server starting with PID {context['server_pid']}")
    
    try:
        yield context
    finally:
        # Clean up happens here when the server is shutting down
        logging.info("====== SERVER SHUTDOWN INITIATED ======")
        logging.info(f"Server PID: {context['server_pid']}")
        
        # DIRECT READ FROM TRACKING FILE
        tracking_file = NASH_SESSION_DIR / "tracked_pids.txt"
        tracked_pids = []
        
        try:
            # Read directly from tracking file
            if tracking_file.exists():
                with open(tracking_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        tracked_pids = [int(p.strip()) for p in content.split(',') if p.strip()]
                        
            print(f"EMERGENCY SHUTDOWN: DIRECT READ FROM {tracking_file}")
            print(f"EMERGENCY SHUTDOWN: FOUND {len(tracked_pids)} PIDS: {','.join(str(p) for p in tracked_pids)}")
        except Exception as e:
            print(f"EMERGENCY SHUTDOWN: ERROR READING TRACKING FILE: {e}")
            
        # Also try the module approach as backup
        try:
            import nash_mcp.constants
            module_pids = nash_mcp.constants.get_all_pids()
            print(f"EMERGENCY SHUTDOWN: MODULE APPROACH FOUND {len(module_pids)} PIDS: {','.join(str(p) for p in module_pids)}")
            
            # Use whichever list has PIDs
            if not tracked_pids and module_pids:
                tracked_pids = module_pids
                print("EMERGENCY SHUTDOWN: USING MODULE PIDS INSTEAD")
        except Exception as e:
            print(f"EMERGENCY SHUTDOWN: ERROR USING MODULE APPROACH: {e}")
            
        logging.info(f"Global process tracker has {len(tracked_pids)} PIDs to clean up")
        
        if tracked_pids:
            logging.info("Tracked PIDs: " + ", ".join(str(pid) for pid in tracked_pids))
            
            # DIRECT KILL ALL TRACKED PIDS
            logging.info("=== TERMINATING TRACKED PROCESSES (SIGTERM) ===")
            
            for pid in tracked_pids:
                try:
                    # Kill process directly with SIGTERM
                    os.kill(pid, signal.SIGTERM)
                    print(f"EMERGENCY SHUTDOWN: SENT SIGTERM TO PID {pid}")
                except ProcessLookupError:
                    print(f"EMERGENCY SHUTDOWN: PID {pid} NOT FOUND (already gone)")
                except Exception as e:
                    print(f"EMERGENCY SHUTDOWN: ERROR SENDING SIGTERM TO PID {pid}: {e}")
                    
            # Also try the module approach
            try:
                nash_mcp.constants.kill_all_pids()
            except Exception as e:
                print(f"EMERGENCY SHUTDOWN: MODULE KILL FAILED: {e}")
            
            # Wait a bit for processes to terminate
            import time
            time.sleep(0.5)
            
            # Check which ones are still running
            remaining_pids = [pid for pid in tracked_pids if psutil.pid_exists(pid)]
            if remaining_pids:
                logging.info(f"{len(remaining_pids)} processes still exist after SIGTERM")
                logging.info("Remaining PIDs: " + ", ".join(str(pid) for pid in remaining_pids))
                
                # DIRECT FORCE KILL WITH SIGKILL
                logging.info("=== FORCE KILLING REMAINING PROCESSES (SIGKILL) ===")
                
                for pid in remaining_pids:
                    try:
                        # Kill process directly with SIGKILL
                        os.kill(pid, signal.SIGKILL)
                        print(f"EMERGENCY SHUTDOWN: SENT SIGKILL TO PID {pid}")
                    except ProcessLookupError:
                        print(f"EMERGENCY SHUTDOWN: PID {pid} NOT FOUND (already gone)")
                    except Exception as e:
                        print(f"EMERGENCY SHUTDOWN: ERROR SENDING SIGKILL TO PID {pid}: {e}")
                        
                # Also try the module approach
                try:
                    nash_mcp.constants.kill_all_pids_forcefully()
                except Exception as e:
                    print(f"EMERGENCY SHUTDOWN: MODULE FORCE KILL FAILED: {e}")
                
                # Wait a bit and verify
                time.sleep(0.5)
                still_running = [pid for pid in remaining_pids if psutil.pid_exists(pid)]
                if still_running:
                    logging.warning(f"{len(still_running)} processes STILL exist after SIGKILL!")
                    logging.warning("Stubborn PIDs: " + ", ".join(str(pid) for pid in still_running))
                else:
                    logging.info("All remaining processes successfully terminated with SIGKILL")
            else:
                logging.info("All processes successfully terminated with SIGTERM")
                
            # FAILSAFE: Scan for any Python processes with our session path in command line
            try:
                our_session_path = str(NASH_SESSION_DIR)
                our_pid = os.getpid()
                
                print(f"EMERGENCY FAILSAFE: Scanning for Python processes with path: {our_session_path}")
                
                # Find any Python processes that might be from our session
                suspects = []
                
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'python' in proc.info['name'].lower() and proc.info['pid'] != our_pid:
                            cmdline = ' '.join(proc.info['cmdline'] or [])
                            if our_session_path in cmdline:
                                suspects.append(proc.info['pid'])
                                print(f"EMERGENCY FAILSAFE: Found suspect process: PID={proc.info['pid']}, CMD={cmdline}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                        continue
                
                if suspects:
                    print(f"EMERGENCY FAILSAFE: Found {len(suspects)} suspect processes - FORCE KILLING")
                    
                    # Force kill these processes
                    for pid in suspects:
                        try:
                            os.kill(pid, signal.SIGKILL)
                            print(f"EMERGENCY FAILSAFE: Sent SIGKILL to suspect process {pid}")
                        except ProcessLookupError:
                            print(f"EMERGENCY FAILSAFE: Suspect process {pid} already gone")
                        except Exception as e:
                            print(f"EMERGENCY FAILSAFE: Error killing suspect process {pid}: {e}")
                else:
                    print("EMERGENCY FAILSAFE: No suspect processes found")
            except Exception as e:
                print(f"EMERGENCY FAILSAFE: Error during process scan: {e}")
        
        else:
            logging.info("No processes in global tracker to clean up")
            
        # Still clean up processes that might be in the old tracking lists
        # This is just for backward compatibility and will be removed in the future
        # Clean up Python processes
        logging.info("=== CLEANING UP TRACKED PYTHON PROCESSES (BACKWARD COMPATIBILITY) ===")
        for proc in list(active_python_processes):
            try:
                if proc.poll() is None:  # Still running
                    proc_pid = proc.pid
                    logging.info(f"Terminating Python subprocess {proc_pid}")
                    os.kill(proc_pid, signal.SIGKILL)  # Direct kill
            except Exception as e:
                logging.error(f"Error terminating Python process: {e}")
        
        # Clean up shell processes
        logging.info("=== CLEANING UP TRACKED SHELL PROCESSES (BACKWARD COMPATIBILITY) ===")
        for proc in list(active_processes):
            try:
                if proc.poll() is None:  # Still running
                    proc_pid = proc.pid
                    logging.info(f"Terminating shell subprocess {proc_pid}")
                    os.kill(proc_pid, signal.SIGKILL)  # Direct kill
            except Exception as e:
                logging.error(f"Error terminating shell process: {e}")
            
        # NUCLEAR OPTION: Look for any orphaned Python processes
        try:
            our_python = sys.executable
            our_pid = os.getpid()
            nash_session_base = str(MAC_SESSIONS_PATH)
            
            print(f"NUCLEAR OPTION: Checking for orphaned Python processes from any Nash session")
            print(f"NUCLEAR OPTION: Our executable: {our_python}")
            print(f"NUCLEAR OPTION: Nash sessions path: {nash_session_base}")
            
            orphans = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower() and proc.info['pid'] != our_pid:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if nash_session_base in cmdline:
                            orphans.append(proc.info['pid'])
                            print(f"NUCLEAR OPTION: Found orphaned process: PID={proc.info['pid']}, CMD={cmdline}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                    continue
            
            if orphans:
                print(f"NUCLEAR OPTION: Found {len(orphans)} orphaned processes - FORCE KILLING")
                
                # Force kill these orphans
                for pid in orphans:
                    try:
                        os.kill(pid, signal.SIGKILL)
                        print(f"NUCLEAR OPTION: Sent SIGKILL to orphaned process {pid}")
                    except ProcessLookupError:
                        print(f"NUCLEAR OPTION: Orphaned process {pid} already gone")
                    except Exception as e:
                        print(f"NUCLEAR OPTION: Error killing orphaned process {pid}: {e}")
            else:
                print("NUCLEAR OPTION: No orphaned processes found")
        
        except Exception as e:
            print(f"NUCLEAR OPTION: Error during orphan process check: {e}")
            
        logging.info("====== PROCESS CLEANUP COMPLETED ======")


# Main MCP server setup and execution
try:
    # Set up logging
    setup_logging()

    logging.info(f"Starting Nash MCP server with session ID: {NASH_SESSION_ID}")

    # Create session directory
    NASH_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created session directory: {NASH_SESSION_DIR}")

    # Create MCP instance with lifespan management
    mcp = FastMCP("Nash", lifespan=nash_lifespan)

    # Register tools
    logging.info("Registering MCP tools")

    # Execute
    mcp.add_tool(execute_command)
    mcp.add_tool(execute_python)
    mcp.add_tool(list_session_files)
    mcp.add_tool(get_file_content)
    mcp.add_tool(edit_python_file)
    mcp.add_tool(list_installed_packages)

    # Fetch
    mcp.add_tool(fetch_webpage)
    
    # Web Automation
    mcp.add_tool(operate_browser)

    # Secrets
    mcp.add_tool(nash_secrets)

    # Tasks
    mcp.add_tool(save_nash_task)
    mcp.add_tool(list_nash_tasks)
    mcp.add_tool(run_nash_task)
    mcp.add_tool(delete_nash_task)
    mcp.add_tool(execute_task_script)
    mcp.add_tool(view_task_details)

    # Start the server
    logging.info("All tools registered, starting MCP server")
    mcp.run()

except Exception as e:
    logging.critical(f"Fatal error in Nash MCP server: {str(e)}")
    logging.critical(f"Traceback: {traceback.format_exc()}")
    print(f"Failed to run server: {str(e)}", file=sys.stderr)
    sys.exit(1)