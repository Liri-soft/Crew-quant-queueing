import logging
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name):
    """Configure a logger with rotation for any module"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Only add handlers if they don't exist
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create log filename from module name (e.g., "services.erlang_staffing" → "erlang_staffing.log")
        module_name = name.split('.')[-1]
        handler = TimedRotatingFileHandler(
            filename=f"logs/{module_name}.log",
            when="midnight",
            interval=1,
            backupCount=1
        )
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Add console handler
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
    
    return logger