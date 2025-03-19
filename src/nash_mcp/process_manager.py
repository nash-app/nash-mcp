import os
import signal
import logging
import psutil
import sys
from pathlib import Path
from typing import List, Set, Optional


class ProcessManager:
    """
    Centralized process management for Nash MCP.

    This class handles tracking, monitoring, and terminating processes
    started by the Nash MCP server. It provides a clean interface for
    process lifecycle management.
    """

    _instance: Optional["ProcessManager"] = None

    @classmethod
    def get_instance(cls) -> "ProcessManager":
        """Get the singleton instance of the ProcessManager."""
        if cls._instance is None:
            raise RuntimeError("ProcessManager not initialized. Call initialize() first.")
        return cls._instance

    @classmethod
    def initialize(cls, session_dir: Path) -> "ProcessManager":
        """Initialize the ProcessManager singleton instance."""
        if cls._instance is None:
            cls._instance = ProcessManager(session_dir)
        return cls._instance

    def __init__(self, session_dir: Path):
        """
        Initialize the process manager.

        Args:
            session_dir: The session directory path where tracking files will be stored
        """
        self.session_dir = session_dir
        self.tracking_file = self.session_dir / "tracked_pids.txt"
        self.server_pid = os.getpid()

        # Ensure tracking file exists
        self._ensure_tracking_file()
        logging.info(f"ProcessManager initialized with tracking file: {self.tracking_file}")
        logging.info(f"Server PID: {self.server_pid}")

    def _ensure_tracking_file(self) -> None:
        """Ensure the tracking file exists and is initialized."""
        try:
            if not self.tracking_file.exists():
                with open(self.tracking_file, "w") as f:
                    f.write("")
                logging.info(f"Created process tracking file: {self.tracking_file}")
        except Exception as e:
            logging.error(f"Error creating tracking file: {e}")

    def add_pid(self, pid: int) -> bool:
        """
        Add a process ID to the tracking system.

        Args:
            pid: The process ID to track

        Returns:
            bool: True if successful, False if failed
        """
        pid = int(pid)  # Ensure it's an integer

        try:
            # Read existing PIDs
            pids = self._read_pids()

            # Add the new PID
            pids.add(pid)

            # Write back to file
            self._write_pids(pids)

            logging.info(f"Added PID {pid} to process tracker. Total PIDs: {len(pids)}")
            return True
        except Exception as e:
            logging.error(f"Error adding PID to tracker: {e}")
            return False

    def remove_pid(self, pid: int) -> bool:
        """
        Remove a process ID from the tracking system.

        Args:
            pid: The process ID to remove

        Returns:
            bool: True if successful, False if failed
        """
        pid = int(pid)  # Ensure it's an integer

        try:
            # Read existing PIDs
            pids = self._read_pids()

            # Remove the PID
            if pid in pids:
                pids.remove(pid)

                # Write back to file
                self._write_pids(pids)

                logging.info(f"Removed PID {pid} from process tracker. Total PIDs: {len(pids)}")
            else:
                logging.info(f"PID {pid} not found in tracker")
            return True
        except Exception as e:
            logging.error(f"Error removing PID from tracker: {e}")
            return False

    def get_all_pids(self) -> List[int]:
        """
        Get all currently tracked process IDs.

        Returns:
            A list of all tracked process IDs
        """
        return list(self._read_pids())

    def clear_pids(self) -> None:
        """Clear all tracked process IDs."""
        try:
            with open(self.tracking_file, "w") as f:
                f.write("")
            logging.info("Cleared all PIDs from tracker")
        except Exception as e:
            logging.error(f"Error clearing PIDs: {e}")

    def _read_pids(self) -> Set[int]:
        """
        Read PIDs from the tracking file.

        Returns:
            A set of process IDs
        """
        pids = set()

        try:
            if self.tracking_file.exists():
                with open(self.tracking_file, "r") as f:
                    content = f.read().strip()
                    if content:
                        pids = set(int(p.strip()) for p in content.split(",") if p.strip())
        except Exception as e:
            logging.error(f"Error reading PIDs from tracker: {e}")

        return pids

    def _write_pids(self, pids: Set[int]) -> None:
        """
        Write PIDs to the tracking file.

        Args:
            pids: A set of process IDs to write
        """
        try:
            with open(self.tracking_file, "w") as f:
                f.write(",".join(str(p) for p in pids))
        except Exception as e:
            logging.error(f"Error writing PIDs to tracker: {e}")

    def kill_process_tree(self, pid: int) -> None:
        """
        Kill a process and all its children.

        Args:
            pid: The process ID to kill
        """
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

        # Always try to remove the PID from tracking regardless of success
        self.remove_pid(pid)

    def terminate_all_processes(self) -> None:
        """
        Terminate all tracked processes with SIGTERM.
        """
        pids = self.get_all_pids()
        logging.info(f"Terminating {len(pids)} tracked processes with SIGTERM")

        for pid in pids:
            try:
                # Try SIGTERM first
                os.kill(pid, signal.SIGTERM)
                logging.info(f"Sent SIGTERM to PID {pid}")
            except ProcessLookupError:
                # Process doesn't exist anymore, remove from tracking
                self.remove_pid(pid)
                logging.info(f"PID {pid} no longer exists, removed from tracking")
            except Exception as e:
                # Other errors, just continue
                logging.error(f"Error sending SIGTERM to PID {pid}: {e}")

    def kill_all_processes(self) -> None:
        """
        Force kill all tracked processes with SIGKILL.
        """
        pids = self.get_all_pids()
        logging.info(f"Force killing {len(pids)} tracked processes with SIGKILL")

        for pid in pids:
            try:
                # Force kill with SIGKILL
                os.kill(pid, signal.SIGKILL)
                logging.info(f"Sent SIGKILL to PID {pid}")

                # Remove from tracking
                self.remove_pid(pid)
            except ProcessLookupError:
                # Process doesn't exist anymore
                self.remove_pid(pid)
                logging.info(f"PID {pid} no longer exists, removed from tracking")
            except Exception as e:
                # Other errors, just continue
                logging.error(f"Error sending SIGKILL to PID {pid}: {e}")

    def kill_all_python_processes(self) -> None:
        """
        Find and kill all Python processes that match our interpreter.

        This is a nuclear option for cleanup.
        """
        our_python = sys.executable
        our_pid = self.server_pid

        try:
            logging.info(f"Scanning for Python processes using our interpreter: {our_python}")
            logging.info(f"Our server PID to exclude: {our_pid}")

            # Get all running Python processes first and log them
            python_processes = []
            logging.info("Listing ALL Python processes currently running:")
            for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
                try:
                    if proc.info["name"] and "python" in proc.info["name"].lower():
                        cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else "unknown"
                        exe = proc.info["exe"] if proc.info["exe"] else "unknown"
                        pid = proc.info["pid"]
                        parent_pid = proc.ppid() if hasattr(proc, "ppid") else "unknown"

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

                        logging.info(
                            f"Python process found: PID={pid}, EXE={exe}, PPID={parent_pid} (parent={parent_name}), CMDLINE={cmdline}"
                        )

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
                        cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else "unknown"
                        pid = proc.info["pid"]
                        logging.info(f"Will kill Python process: PID={pid}, CMDLINE={cmdline}")

                        # Kill the process tree
                        self.kill_process_tree(pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    except Exception as e:
                        logging.error(f"Error killing Python process {proc.info['pid']}: {e}")
            else:
                logging.info("No matching Python processes found to kill")
        except Exception as e:
            logging.error(f"Error in kill_all_python_processes: {e}")

    def find_orphaned_processes(self, session_base_path: str = None) -> None:
        """
        Find and kill orphaned processes from any Nash session.

        This is an emergency failsafe for cleanup.

        Args:
            session_base_path: Optional base path for all Nash sessions
        """
        our_python = sys.executable
        our_pid = self.server_pid
        our_session_path = str(self.session_dir)

        try:
            target_paths = [our_session_path]
            if session_base_path:
                target_paths.append(session_base_path)

            logging.info(f"EMERGENCY FAILSAFE: Scanning for orphaned processes with paths: {target_paths}")

            # Find any Python processes that might be from our session
            suspects = []

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if "python" in proc.info["name"].lower() and proc.info["pid"] != our_pid:
                        cmdline = " ".join(proc.info["cmdline"] or [])

                        # Check if the command line contains any of our target paths
                        if any(path in cmdline for path in target_paths):
                            suspects.append(proc.info["pid"])
                            logging.info(
                                f"EMERGENCY FAILSAFE: Found suspect process: PID={proc.info['pid']}, CMD={cmdline}"
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                    continue

            if suspects:
                logging.info(f"EMERGENCY FAILSAFE: Found {len(suspects)} suspect processes - FORCE KILLING")

                # Force kill these processes
                for pid in suspects:
                    try:
                        os.kill(pid, signal.SIGKILL)
                        logging.info(f"EMERGENCY FAILSAFE: Sent SIGKILL to suspect process {pid}")
                    except ProcessLookupError:
                        logging.info(f"EMERGENCY FAILSAFE: Suspect process {pid} already gone")
                    except Exception as e:
                        logging.error(f"EMERGENCY FAILSAFE: Error killing suspect process {pid}: {e}")
            else:
                logging.info("EMERGENCY FAILSAFE: No suspect processes found")
        except Exception as e:
            logging.error(f"EMERGENCY FAILSAFE: Error during process scan: {e}")

    def cleanup(self, session_base_path: str = None) -> None:
        """
        Comprehensive cleanup of all managed processes.

        This method attempts a full cleanup using all available strategies.
        It should be called during server shutdown.

        Args:
            session_base_path: Optional base path for all Nash sessions for orphan detection
        """
        logging.info("====== PROCESS CLEANUP INITIATED ======")
        logging.info(f"Server PID: {self.server_pid}")

        # 1. Terminate all tracked processes with SIGTERM first
        self.terminate_all_processes()

        # Give processes time to terminate gracefully
        import time

        time.sleep(0.5)

        # 2. Kill any remaining processes with SIGKILL
        self.kill_all_processes()

        # 3. Find and kill any orphaned Python processes
        self.find_orphaned_processes(session_base_path)

        # 4. As a nuclear option, kill any Python process matching our interpreter
        self.kill_all_python_processes()

        logging.info("====== PROCESS CLEANUP COMPLETED ======")
