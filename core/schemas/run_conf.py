schema = {
    "name": {
        "required": True,
        "type": "string",
    },
    "benchmarks": {"required": True, "type": ["string", "list"]},
    "metrics": {
        "required": True,
        "type": "string",
    },
}
