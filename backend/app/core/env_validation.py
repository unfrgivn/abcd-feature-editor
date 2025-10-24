import logging
import os
import sys

logger = logging.getLogger(__name__)


REQUIRED_ENV_VARS = [
    "GOOGLE_API_KEY",
    "MODEL_NAME",
    "PROJECT_ID",
    "APP_NAME",
    "DEFAULT_USER_ID",
    "DEFAULT_SESSION_ID",
    "CONFIG_PATH",
    "GCS_SCRATCH_BUCKET",
    "GCS_FINAL_BUCKET",
    "GCS_PROJECT_ID",
    "DATABASE_PATH"
]

OPTIONAL_ENV_VARS = [
    "GOOGLE_GENAI_USE_VERTEXAI",
    "MODEL_NAME2",
    "ADS_PLATFORM",
    "DATASET_NAME",
    "TABLE_NAME",
    "RUNNING_AS_API"
]


def validate_environment() -> bool:
    missing_vars = []
    
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("Please set these variables in backend/app/.env")
        return False
    
    logger.info("Environment validation passed")
    
    missing_optional = [var for var in OPTIONAL_ENV_VARS if not os.getenv(var)]
    if missing_optional:
        logger.warning("Missing optional environment variables:")
        for var in missing_optional:
            logger.warning(f"  - {var}")
    
    return True


def validate_environment_or_exit():
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)
