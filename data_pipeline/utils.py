import logging
from pathlib import Path
logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    """Configure logging for the pipeline."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s — %(message)s", datefmt="%H:%M:%S")

def validate_input(filepath):
    """Check whether the input path exists and is a file."""
    file_path = Path(filepath)
    if file_path.is_file():
        logger.info(f"Input file validated: {file_path}")
        return True
    else:
        logger.error(f"Input file not found: {file_path}")
        return False