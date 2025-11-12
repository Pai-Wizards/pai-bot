import json
import aiofiles

from datetime import datetime

from config.settings import TAKES_FILE


async def load_takes_json():
    try:
        async with aiofiles.open(TAKES_FILE, "r") as f:
            content = await f.read()
            return json.loads(content)
    except FileNotFoundError:
        # Return empty structure if file doesn't exist
        return {}
    except Exception as e:
        import logging
        logger = logging.getLogger("bot_logger")
        logger.error(f"Error loading takes JSON: {e}")
        return {}

async def save_takes_json(data):
    try:
        async with aiofiles.open(TAKES_FILE, "w") as f:
            await f.write(json.dumps(data, indent=2))
    except Exception as e:
        import logging
        logger = logging.getLogger("bot_logger")
        logger.error(f"Error saving takes JSON: {e}")

def days_since_last_take(last_take):
    if last_take is None:
        return 0
    last_take = datetime.fromisoformat(last_take)
    return (datetime.now() - last_take).days
