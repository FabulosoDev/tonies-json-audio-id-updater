import os
from logger_factory import DefaultLoggerFactory

logger = DefaultLoggerFactory.get_logger(__name__)

class ToniesJsonRepo:
    def __init__(self):
        """Initialize ToniesJsonRepo"""
        self.tonies_json_repo_path = os.getenv("TONIES_JSON_REPO_PATH")
        if not self.tonies_json_repo_path:
            logger.error("TONIES_JSON_REPO_PATH environment variable not set")
            raise ValueError("TONIES_JSON_REPO_PATH environment variable not set")

    def find_yaml_by_model(self, model):
        """Returns the found yaml file path for the given model."""
        if not model:
            return None
        for root, _, files in os.walk(self.tonies_json_repo_path):
            for file in files:
                if file == model + ".yaml":
                    logger.debug(f"Found yaml file for model {model}: {file}")
                    return os.path.join(root, file)
        return None