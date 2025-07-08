class _Base:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)


class Div(_Base):
    pass


class Img(_Base):
    pass


class I(_Base):
    pass
