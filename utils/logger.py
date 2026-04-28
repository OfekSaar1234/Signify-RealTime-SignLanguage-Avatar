import logging
import sys
import os
from datetime import datetime

def setup_logger(name="Signify"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s', datefmt='%H:%M:%S')
        
        # Console Handler with timeline formatting
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File Handler (saving logs to a 'logs' folder)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.path.join(logs_dir, f"signify_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG) # Save all debug and info messages to the file
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

# Global instance for easy import
logger = setup_logger()
