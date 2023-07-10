schema = {
    "info": {
        "required": True,
        "type": "dict",
        "schema": {
            "name": {"required": True, "type": "string"},
            "description": {"required": True, "type": "string"},
            "benchmark": {"required": True, "type": "string"},
            "run_args": {"required": True, "type": "string"},
            "iterations": {"required": False, "type": "integer", "default": 1},
        },
    }
}
