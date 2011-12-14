from zope.component.interfaces import IObjectEvent
from zope.interface import implements, Attribute


class ObjectEvent(object):

    """ Initialize event """

    def __init__(self, obj, parent):

        self.object = obj
        self.parent = parent


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


class ContentAdded(ObjectEvent):

    """ Object is added """

    implements(IObjectAddedEvent)

    def __init__(self, object, parent):
        self.object = object
        self.parent = parent


class ContentRemoved(ObjectEvent):

    """ Object is removed """

    implements(IObjectRemovedEvent)

    def __init__(self, object, parent):
        self.object = object
        self.parent = parent


class ContentChanged(ObjectEvent):

    """ Object is changed """

    implements(IObjectChangedEvent)

    def __init__(self, object):
        self.object = object
