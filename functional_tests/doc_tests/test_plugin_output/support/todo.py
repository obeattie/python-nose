from nose.plugins.errorclass import ErrorClass, ErrorClassPlugin


class Todo(Exception):
    pass


class TodoPlugin(ErrorClassPlugin):
    enabled = True
    todo = ErrorClass(Todo, label='TODO', isfailure=True)

    def options(self, parser, env=None):
        pass

    def configure(self, options, conf):
        pass
