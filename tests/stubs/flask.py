class Flask:
    def __init__(self, *args, **kwargs):
        self.config = {}
        self.teardown_funcs = []
    def teardown_appcontext(self, func):
        self.teardown_funcs.append(func)
        return func

session = {}
