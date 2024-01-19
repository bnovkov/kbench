schema = {
    "info": {
        "required": True,
        "type": "dict",
        "schema": {
            "name": {"required": True, "type": "string"},
            "description": {"required": True, "type": "string"},
            "prebuilt": {"required": False, "type": "boolean", "default" : False},
        },
    },
    "src": {
        "required": False,
        "type": "dict",
        "schema": {
            "fetch": {
                "required": False,
                "type": "dict",
                "schema": {
                    "url": {"required": True, "type": "string"},
                },
            },
            "git": {
                "required": False,
                "type": "dict",
                "schema": {
                    "url": {"required": True, "type": "string"},
                },
            },

        },
    },
    "setup": {
        "required": False,
        "type": "dict",
        "schema": {"builddir": {"required": False, "type": "string"},
                   "buildcmd": {"required": True, "type": "string"}},
    },
    "run": {
        "required": True,
        "type": "dict",
        "schema": {
            "make": {
                "required": False,
                "type": "dict",
                "schema": {
                    "rootdir": {"required": True, "type": "string"},
                    "ncpu": {"required": False, "type": "integer"},
                    "builddir": {"required": False, "type": "string"},
                    "env": {
                        "required": False,
                        "type": "dict",
                    },
                },
            },
            "exec": {
                "required": False,
                "type": "dict",
                "schema": {
                    "cmds": {"required": True, "type": "list"},
                },
            }
        },
    },
}
