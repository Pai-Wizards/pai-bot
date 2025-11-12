import time
import logging

logger = logging.getLogger("bot_logger")
cooldowns = {}

def on_cooldown(user_id: int, cooldown_time: int, admin_id=None):
    logger.debug(f"Checking cooldown for user ID: {user_id}")
    if admin_id and user_id == admin_id:
        logger.debug("Admin bypass activated")
        return False
    last_trigger = cooldowns.get(user_id, 0)
    if time.time() - last_trigger > cooldown_time:
        cooldowns[user_id] = time.time()
        logger.debug("User not in cooldown")
        return False
    logger.debug("User in cooldown")
    return True
