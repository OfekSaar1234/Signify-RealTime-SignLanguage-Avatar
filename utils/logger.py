import logging
import sys
import os
from datetime import datetime

def setup_logger(name="Signify", log_subdir=None):
    """
    Creates and returns a configured logger instance.
    
    Args:
        name: Logger name (appears in log output).
        log_subdir: Optional subdirectory inside 'logs/' to organize log files 
                    (e.g., 'cloud' for cloud pipeline runs).
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Rich formatter with thread name — essential for multi-threaded pipeline debugging
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] [%(threadName)-12s] [%(module)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler with timeline formatting
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File Handler (saving logs to a 'logs' folder)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, "logs")
        if log_subdir:
            logs_dir = os.path.join(logs_dir, log_subdir)
        os.makedirs(logs_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = os.path.join(logs_dir, f"signify_{timestamp}.log")
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG) # Save all debug and info messages to the file
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        logger.info(f"Log file created: {log_file}")
        
    return logger


def setup_cloud_logger():
    """
    Creates a dedicated logger for the Cloud Pipeline (EC2 runs).
    Writes to logs/cloud/ with full DEBUG-level detail including HTTP traffic,
    timing, S3 operations, and per-word progress tracking.
    """
    return setup_logger(name="Signify.Cloud", log_subdir="cloud")


# Global instance for easy import (local pipeline / main app)
logger = setup_logger()
