class _Base:
    def __init__(self, *args, **kwargs):
        if "children" in kwargs:
            self.children = kwargs.pop("children")
        elif len(args) == 1:
            self.children = args[0]
        else:
            self.children = list(args)
        for k, v in kwargs.items():
            setattr(self, k, v)


class Div(_Base):
    pass


class H5(_Base):
    pass


class H6(_Base):
    pass


class Tr(_Base):
    pass


class Td(_Base):
    pass


class Th(_Base):
    pass


class Thead(_Base):
    pass


class Tbody(_Base):
    pass


class Br(_Base):
    pass


class Small(_Base):
    pass


class Strong(_Base):
    pass


class Span(_Base):
    pass


class Img(_Base):
    pass


class I(_Base):
    pass
