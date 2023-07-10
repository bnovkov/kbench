class DictObj:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class DummyDict(dict):
    def __getitem__(self, item):
        return ""


class ConfigDummyDict(dict):
    def __getitem__(self, item):
        return DummyDict()
