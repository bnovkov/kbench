sysctlSchema = {
    "type": "dict",
    "schema": {
        "oid": {"required": True, "type": "string"},
        "sampling_rate": {"required": False, "type": "integer"},
    },
}

psSchema = {
    "type": "dict",
    "schema": {
        "command": {"required": True, "type": "string"},
        "stats": {"required": True, "type": "list"},
    },
}

metricsSchema = {
    "sysctl": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "oid": {"required": True, "type": "string"},
                "sampling_rate": {"required": False, "type": "integer"},
            },
        },
    },
    "ps": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "command": {"required": True, "type": "string"},
                "stats": {"required": True, "type": "list"},
            },
        },
    },
}

schema = {
    "diff": {"type": "dict", "schema": metricsSchema},
    "continuous": {"type": "dict", "schema": metricsSchema},
}
