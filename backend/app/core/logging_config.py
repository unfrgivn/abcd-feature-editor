import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> None:
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path(__file__).parent.parent / "logs" / "app.log",
                mode="a"
            )
        ]
    )
    
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
