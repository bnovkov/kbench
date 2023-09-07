class DummyDict(dict):
    def __getitem__(self, item):
        return ""


class ConfigDummyDict(dict):
    def __getitem__(self, item):
        return DummyDict()
