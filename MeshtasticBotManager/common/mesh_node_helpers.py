from datetime import datetime, timezone

BROADCAST_ID = 0xFFFFFFFF


def meshtastic_id_to_hex(meshtastic_id: int) -> str:
    """
    Convert a Meshtastic ID (integer form) to hex representation (!abcdef12)
    """
    if meshtastic_id == BROADCAST_ID:
        return "^all"

    return f"!{meshtastic_id:08x}"


def meshtastic_hex_to_int(node_id: str) -> int:
    """
    Convert a Meshtastic ID (hex representation) to integer form
    """
    if node_id == "^all":
        return BROADCAST_ID

    return int(node_id[1:], 16)


def pretty_print_last_heard(last_heard_timestamp: int | datetime) -> str:
    if isinstance(last_heard_timestamp, datetime):
        last_heard = last_heard_timestamp
    elif isinstance(last_heard_timestamp, int):
        last_heard = datetime.fromtimestamp(last_heard_timestamp, timezone.utc)
    else:
        return "Unknown"

    now = datetime.now(timezone.utc)
    delta = now - last_heard

    if delta.total_seconds() < 0:
        return "0s ago"

    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return f"{delta.seconds}s ago"
