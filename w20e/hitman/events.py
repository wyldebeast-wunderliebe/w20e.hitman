from zope.component.interfaces import IObjectEvent
from zope.interface import implementer, Attribute


class ObjectEvent(object):

    """ Initialize event """

    def __init__(self, obj, parent, request=None):

        self.object = obj
        self.parent = parent
        self.request = request


class IObjectAddedEvent(IObjectEvent):

    """ Interface for added objects """

    object = Attribute('The object being added')
    parent = Attribute('The folder to which the object is being added')


class IObjectRemovedEvent(IObjectEvent):

    """ Interface for removed objects """

    object = Attribute('The object being added')
    parent = Attribute('The folder from which the object is removed')


class IObjectChangedEvent(IObjectEvent):

    """ Interface for changed objects """


@implementer(IObjectAddedEvent)
class ContentAdded(ObjectEvent):

    """ Object is added """


@implementer(IObjectRemovedEvent)
class ContentRemoved(ObjectEvent):

    """ Object is removed """


@implementer(IObjectChangedEvent)
class ContentChanged(ObjectEvent):

    """ Object is changed """

    def __init__(self, object, request=None):
        self.object = object
        self.request = request
