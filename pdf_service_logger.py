import logging
import sys

# Set up logging to go to stdout, which Lambda captures
logging.basicConfig(
    level=logging.INFO,  # Capture INFO-level logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # Ensure logs are written to stdout
)

logger = logging.getLogger()
