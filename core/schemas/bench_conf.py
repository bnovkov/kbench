schema = {
    "info": {
        "required": True,
        "type": "dict",
        "schema": {
            "name": {"required": True, "type": "string"},
            "description": {"required": True, "type": "string"},
        },
    },
    "files": {
        "required": False,
        "type": "dict",
        "schema": {
            "rootdir": {"required": True, "type": "string"},
            "fetch": {
                "required": False,
                "type": "dict",
                "schema": {
                    "filename": {"required": True, "type": "string"},
                    "url": {"required": True, "type": "string"},
                },
            },
        },
    },
    "setup": {
        "required": False,
        "type": "dict",
        "schema": {"builddir": {"required": False, "type": "string"}},
    },
    "run": {
        "required": True,
        "type": "dict",
        "schema": {
            "runner": {"required": True, "type": "string"},
            "tmpfiledir": {"required": False, "type": "string"},
            "env": {
                "required": False,
                "type": "dict",
            },
        },
    },
}
