from builtins import object
from zope.interface.interfaces import IObjectEvent
from zope.interface import implementer, Attribute


class ObjectEvent(object):

    """Initialize event"""

    def __init__(self, obj, parent):

        self.object = obj
        self.parent = parent


class IObjectAddedEvent(IObjectEvent):

    """Interface for added objects"""

    object = Attribute("The object being added")
    parent = Attribute("The folder to which the object is being added")


class IObjectRemovedEvent(IObjectEvent):

    """Interface for removed objects"""

    object = Attribute("The object being added")
    parent = Attribute("The folder from which the object is removed")


class IObjectChangedEvent(IObjectEvent):

    """Interface for changed objects"""


class IObjectCopiedEvent(IObjectEvent):

    """Interface for copied objects"""

    object = Attribute("The new object that was added")
    source = Attribute("The original object")


@implementer(IObjectAddedEvent)
class ContentAdded(ObjectEvent):

    """Object is added"""


@implementer(IObjectRemovedEvent)
class ContentRemoved(ObjectEvent):

    """Object is removed"""


@implementer(IObjectChangedEvent)
class ContentChanged(ObjectEvent):

    """Object is changed"""

    def __init__(self, object):
        self.object = object


@implementer(IObjectCopiedEvent)
class ContentCopied(ObjectEvent):

    """Object is copied"""

    def __init__(self, object, source):
        self.object = object
        self.source = source
