import os
from typing import Any

from loguru import logger


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle Lambda function invocation."""
    logger.info(f"Received event: {event}")

    # Received event: {'document_id': '1706.03762v7', 
    #                   's3_path': 's3://step-functions-16c78fbd7d18453b8745a2047e875e14/1706.03762v7.pdf'}

    try:
        object_key = event["s3_path"].split("://")[1]
        bucket_name = object_key.split("/")[0]

        # Extract file name and extension
        filename = os.path.basename(object_key)
        name, extension = os.path.splitext(filename)

        metadata = {
            "bucket_name": bucket_name,
            "s3_path": object_key,
            "file_name": name,
            "file_extension": extension,
        }

        logger.info(f"Extracted metadata: {metadata}")
        return metadata

    except KeyError as e:
        logger.error(f"Missing expected key: {e}")
        raise
