class Annotated:
    def __init__(self, data, annotation):
        self.data = data
        self.annotation = annotation

    def __getattr__(self, name):
        def method(*args, **kwargs):
            return getattr(self.data, name)(*args, **kwargs)

        return method

    def __str__(self):
        return f"{str(self.annotation)}({str(self.data)})"
