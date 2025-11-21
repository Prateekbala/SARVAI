import logging
import sys
from pythonjsonlogger import jsonlogger
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    formatter = jsonlogger.JsonFormatter(log_format)
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(logs_dir / "app.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    
    root_logger.info("Structured logging configured", extra={"log_level": log_level})
