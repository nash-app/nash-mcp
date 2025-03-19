import os
import signal
import logging
import psutil
from pathlib import Path
from typing import List, Optional


class ProcessManager:
    """
    Centralized process management for Nash MCP.

    This class handles tracking, monitoring, and terminating processes
    started by the Nash MCP server.
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
            session_dir: The session directory path
        """
        self.session_dir = session_dir
        self.server_pid = os.getpid()

        # In-memory tracking of process IDs
        self.tracked_pids = set()

        logging.info(f"ProcessManager initialized with in-memory tracking")
        logging.info(f"Server PID: {self.server_pid}")

    def add_pid(self, pid: int) -> bool:
        """
        Add a process ID to the in-memory tracking system.

        Args:
            pid: The process ID to track

        Returns:
            bool: True if successful, False if failed
        """
        try:
            pid = int(pid)  # Ensure it's an integer
            self.tracked_pids.add(pid)
            logging.info(f"Added PID {pid} to process tracker. Total PIDs: {len(self.tracked_pids)}")
            return True
        except Exception as e:
            logging.error(f"Error adding PID to tracker: {e}")
            return False

    def remove_pid(self, pid: int) -> bool:
        """
        Remove a process ID from the in-memory tracking system.

        Args:
            pid: The process ID to remove

        Returns:
            bool: True if successful, False if failed
        """
        try:
            pid = int(pid)  # Ensure it's an integer
            if pid in self.tracked_pids:
                self.tracked_pids.remove(pid)
                logging.info(f"Removed PID {pid} from process tracker. Total PIDs: {len(self.tracked_pids)}")
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
        return list(self.tracked_pids)

    def clear_pids(self) -> None:
        """Clear all tracked process IDs."""
        try:
            previous_count = len(self.tracked_pids)
            self.tracked_pids.clear()
            logging.info(f"Cleared all {previous_count} PIDs from tracker")
        except Exception as e:
            logging.error(f"Error clearing PIDs: {e}")

    def terminate_process(self, pid: int) -> None:
        """
        Terminate a process directly using SIGTERM and SIGKILL.

        Args:
            pid: The process ID to terminate
        """
        try:
            # Simple, direct process termination - first with SIGTERM
            os.kill(pid, signal.SIGTERM)
            logging.info(f"Sent SIGTERM directly to PID {pid}")

            # Give it a moment to terminate
            import time

            time.sleep(0.5)

            # Check if it's still running
            if psutil.pid_exists(pid):
                # Process is still alive, send SIGKILL
                os.kill(pid, signal.SIGKILL)
                logging.info(f"Sent SIGKILL directly to PID {pid}")

        except ProcessLookupError:
            logging.info(f"Process {pid} not found")
        except Exception as e:
            logging.error(f"Error terminating process {pid}: {e}")

        # Always remove the PID from tracking
        self.remove_pid(pid)

    def terminate_all_processes(self) -> None:
        """
        Terminate all tracked processes with SIGTERM and SIGKILL if needed.
        """
        # Make a copy of the PIDs before iterating, since we might modify the set during iteration
        pids = list(self.tracked_pids)
        logging.info(f"Terminating {len(pids)} tracked processes")

        for pid in pids:
            self.terminate_process(pid)

    def cleanup(self) -> None:
        """
        Cleanup all tracked processes.

        This method terminates all tracked processes.
        It should be called during server shutdown.
        """
        logging.info("====== PROCESS CLEANUP INITIATED ======")
        logging.info(f"Server PID: {self.server_pid}")

        # Terminate all tracked processes
        self.terminate_all_processes()

        logging.info("====== PROCESS CLEANUP COMPLETED ======")
