from builtins import object
class Registry(object):

    """ Global registry for content types """

    content_types = {}

    @staticmethod
    def register(name, clazz):

        Registry.content_types[name] = clazz

    @staticmethod
    def get(name):

        return Registry.content_types.get(name, None)
