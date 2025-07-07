class Swagger:
    def __init__(self, app=None, template=None):
        if app is not None:
            app.swagger = True
        self.template = template
