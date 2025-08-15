class Location:
    def __init__(self, *a, **k):
        pass


class Download:
    def __init__(self, *a, **k):
        pass


class Dropdown:
    def __init__(self, *args, **kwargs):
        self.children = list(args)
        for k, v in kwargs.items():
            setattr(self, k, v)


class Store:
    def __init__(self, *args, **kwargs):
        self.children = list(args)
        for k, v in kwargs.items():
            setattr(self, k, v)


class Link:
    def __init__(self, *args, **kwargs):
        self.children = list(args)
        for k, v in kwargs.items():
            setattr(self, k, v)
