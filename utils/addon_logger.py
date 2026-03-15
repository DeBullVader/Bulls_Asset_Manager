import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.INFO, max_size=1048576, backups=5):
    """Sets up a rotating file logger with a stdout stream handler.

    Args:
        name (str): Name of the logger.
        log_file (str): Path to the log file.
        level (int, optional): Logging level. Defaults to logging.INFO.
        max_size (int, optional): Max size of log file in bytes. Defaults to 1048576 (1MB).
        backups (int, optional): Number of backup files to keep. Defaults to 5.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Rotating file handler
    file_handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backups)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream handler → VSCode terminal (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

# Determine path to addon directory
addon_directory = os.path.dirname(os.path.dirname(__file__))
print(addon_directory)
error_dir =f'{addon_directory}{os.sep}error_logs'
# Set up the logger (adjust the file path as needed)
log_file_path = os.path.join(error_dir, 'error_log.txt')
if not os.path.exists(error_dir):
    os.mkdir(error_dir)
addon_logger = setup_logger('addon_logger', log_file_path)


def unregister():
    for handler in addon_logger.handlers[:]:
        handler.close()
        addon_logger.removeHandler(handler)