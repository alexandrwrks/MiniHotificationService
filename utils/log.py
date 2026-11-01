from loguru import logger

# Loguru writes to stderr so delivery errors appear in docker compose logs.
rabbitmq_logger = logger.bind(component="notifications")
