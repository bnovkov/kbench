schema = {
    "sysctl": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {"required": True, "type": "string"},
                "mode": {"required": False, "type": "string"},
                "sampling_rate": {"required": False, "type": "integer"},
                "oids": {"required": True, "type": "list"},
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
    "dtrace": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "required": True,
                    "type": "string",
                },
                "scripts": {
                    "required": True,
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "name": {"required": True, "type": "string"},
                            "src": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
}
