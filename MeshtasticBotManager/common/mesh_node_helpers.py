def meshtastic_id_to_hex(meshtastic_id: int) -> str:
    """
    Convert a Meshtastic ID (integer form) to hex representation (!abcdef12)
    """
    return f"!{meshtastic_id:08x}"


def meshtastic_hex_to_int(node_id: str) -> int:
    """
    Convert a Meshtastic ID (hex representation) to integer form
    """
    return int(node_id[1:], 16)

