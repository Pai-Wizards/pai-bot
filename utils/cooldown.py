import time

cooldowns = {}


def on_cooldown(user_id: int, cooldown_time: int, admin_id=None):
    print(f"User ID: {user_id}")
    if admin_id and user_id == admin_id:
        print("Admin bypass")
        return False
    last_trigger = cooldowns.get(user_id, 0)
    if time.time() - last_trigger > cooldown_time:
        cooldowns[user_id] = time.time()
        print("User not in cooldown")
        return False
    print("User in cooldown")
    return True
