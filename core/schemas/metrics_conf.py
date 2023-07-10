schema = {
    "sysctl": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "oid": {"required": True, "type": "string"},
                "mode": {"required": False, "type": "string"},
                "sampling_rate": {"required": False, "type": "integer"},
            },
        },
    }
}
