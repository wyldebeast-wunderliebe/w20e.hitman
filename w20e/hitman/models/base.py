from datetime import datetime

from BTrees.OOBTree import OOBTree  # type: ignore
from persistent import Persistent
from persistent.mapping import PersistentMapping
from slugify import slugify
from w20e.forms.formdata import FormData
from w20e.forms.utils import find_file
from w20e.forms.xml.factory import XMLFormFactory
from w20e.forms.xml.formfile import FormFile
from zope.component import getSiteManager
from zope.interface import Interface, implementer

from w20e.hitman.utils import object_to_path

from ..events import ContentAdded, ContentChanged, ContentRemoved
from .exceptions import UniqueConstraint


class IContent(Interface):

    """Marker for base content"""


class IFolder(IContent):

    """Marker for folderish content"""


class Base(object):

    """Base content, should be extended for real content"""

    def __bool__(self):
        return True

    def __init__(self, content_id, data_attr_name="_DATA", data=None):
        if not data:
            data = {}

        # sanity check.. ID cannot be empty
        if not content_id:
            raise Exception("ID should not be empty")

        self._id = content_id
        self.data_attr_name = data_attr_name
        setattr(self, data_attr_name, OOBTree(data))
        self._created = datetime.now()
        self._changed = datetime.now()

    @property
    def id(self):
        return self._id

    def set_id(self, id):
        self._id = id

    @property
    def owner(self):
        """get the creator userid"""

        return getattr(self, "_owner", "")

    @owner.setter
    def owner(self, value):
        """set the creator userid"""

        self._owner = value
        self._p_changed = 1

    @property
    def content_type(self):
        return self.__class__.__name__.lower()

    def allowed_content_types(self, request):
        return []

    @property
    def base_id(self):
        return self.content_type

    @property
    def has_parent(self):
        return getattr(self, "__parent__", None)

    @property
    def _data_(self):
        """Wrap data in formdata container. Keep it volatile though,
        so as not to pollute the DB."""

        try:
            return self._v_data
        except:
            data = getattr(self, self.data_attr_name)

            # # migrate old hashmaps to OOBTree if necessary
            # if not isinstance(data, OOBTree):
            #     data = OOBTree(data)
            #     setattr(self, self.data_attr_name, data)

            self._v_data = FormData(data=data)
            return self._v_data

    def set_attribute(self, name, value):
        """store an attribut in a low level manner"""

        data = getattr(self, self.data_attr_name)
        data[name] = value
        self._changed = datetime.now()
        self._p_changed = 1
        # remove volatile cached data
        try:
            del self._v_data
        except:
            pass  # no worries.we didn't have the cached value

    def _form_(self, request):
        """Volatile form"""

        try:
            return self._v_form
        except:
            form = find_file(self.edit_form, self.__class__)
            xmlff = XMLFormFactory(FormFile(form).filename)
            self._v_form = xmlff.create_form(action="")

            return self._v_form

    @property
    def title(self):
        return self.id

    @property
    def created(self):
        return self._created

    @property
    def changed(self):
        return self._changed

    @property
    def root(self):
        _root = self

        while getattr(_root, "__parent__", None) is not None:
            if _root == _root.__parent__:
                break
            _root = _root.__parent__

        return _root

    @classmethod
    def defaults(self):
        return {}

    @property
    def path(self):
        """Return path from root as list of id's"""

        return object_to_path(self, as_list=True)

    @property
    def dottedpath(self):
        """Return path as dot separated string"""

        return object_to_path(self, path_sep=".", as_list=False)


@implementer(IContent)
class BaseContent(Persistent, Base):

    """Base content, should be extended for real content"""

    def __init__(self, content_id, data=None, **kwargs):
        if not data:
            data = {}

        Persistent.__init__(self)
        Base.__init__(self, content_id, data=data)

    def __repr__(self):
        """return the ID as base representation"""

        return self.id


@implementer(IFolder)
class BaseFolder(PersistentMapping, Base):

    """Base folder"""

    def __init__(self, content_id, data=None, **kwargs):
        if not data:
            data = {}

        PersistentMapping.__init__(self)
        Base.__init__(self, content_id, data=data)
        self._order = []

    def add_content(self, content, emit_event=True):
        # don't replace the content
        if content.id in self:
            raise UniqueConstraint(
                "an item with this ID already exists at \
                    this level"
            )

        content.__parent__ = self
        content.__name__ = content.id
        self[content.id] = content
        self._order.append(content.id)

        if emit_event:
            sm = getSiteManager()
            sm.notify(ContentAdded(content, self))

    def rename_content(self, id_from, id_to, emit_event=True):
        """Move object at id_from to id_to key"""

        normalized_id_to = self._normalize_id(id_to)

        if normalized_id_to in self:
            raise UniqueConstraint(
                "an item with this ID already exists at \
                    this level"
            )

        content = self.get(id_from, None)

        if content is None:
            return False

        del self[id_from]

        content._id = normalized_id_to
        content.__name__ = normalized_id_to

        # retain order
        if id_from in self._order:
            self._order[self._order.index(id_from)] = normalized_id_to

        self[content.id] = content

        if emit_event:
            sm = getSiteManager()
            sm.notify(ContentChanged(content))

            # all children objects will now have to update the path
            # (location) index. This could be speeded up by signalling
            # that only the path changed and reindex could be more specific
            if IFolder.providedBy(content):
                for child in content.find_content():
                    sm.notify(ContentChanged(child))

    def remove_content(self, content_id):
        try:
            content = self.get(content_id, None)
            del self[content_id]
            self._order.remove(content_id)

            sm = getSiteManager()
            sm.notify(ContentRemoved(content, self))
            # all children objects will now have to update the path
            # (location) index. This could be speeded up by signalling
            # that only the path changed and reindex could be more specific
            if IFolder.providedBy(content):
                for child in content.find_content():
                    sm.notify(ContentRemoved(child, child.__parent__))

            return content
        except:
            return None

    def get_content(self, content_id, content_type=None):
        obj = self.get(content_id, None)

        if content_type:
            if getattr(obj, "content_type", None) == content_type:
                return obj

            else:
                return None

        return obj

    def _list_content_ids(self, **kwargs):
        """
        Return all content IDs.
        NOTE: also returns temporary object IDs
        """

        all_ids = list(self.keys())

        def custom_sort_key(item):
            max_order = len(self._order) + 1
            return (self._order.index(item) if item in self._order else max_order, item)

        all_ids.sort(key=custom_sort_key)

        return all_ids

    def list_content(self, content_type=None, iface=None, **kwargs):
        """List content of this folder. If content_type is given,
        list only these things.
        """

        all_content = []

        if content_type:
            if isinstance(content_type, str):
                content_type = [content_type]

            all_content = [
                obj
                for obj in list(self.values())
                if getattr(obj, "content_type", None) in content_type
            ]
        if iface:
            all_content = [obj for obj in list(self.values()) if iface.providedBy(obj)]

        if not (content_type or iface):
            all_content = list(self.values())

        if kwargs.get("order_by", None):
            reverse = kwargs.get("order_by_reversed", 0)
            all_content.sort(
                key=lambda x: getattr(x, kwargs["order_by"]), reverse=reverse
            )
        else:
            all_content.sort(key=lambda x: x.id)

        return all_content

    def find_content(self, content_type=None):
        """Find content recursively from the given folder. Use it
        wisely..."""

        found = self.list_content(content_type=content_type)

        # recurse through folderish types.
        folders = self.list_content(iface=IFolder)

        for sub in folders:
            try:
                found += sub.find_content(content_type=content_type)
            except:
                # looks like it's not a folder...
                pass

        return found

    def _normalize_id(self, id):
        """change all non-letters and non-numbers to dash"""
        # id = id.lower()
        # id = re.sub('[^-a-z0-9_]+', '-', id)
        # return id
        return slugify(id)

    def generate_content_id(self, base_id):
        base_id = self._normalize_id(base_id)

        if base_id not in self:
            return base_id

        cnt = 1

        while "%s_%s" % (base_id, cnt) in self:
            cnt += 1

        return "%s_%s" % (base_id, cnt)

    def move_content(self, content_id, delta):
        """Move the content in the order by delta, where delta may be
        negative"""

        curr_idx = self._order.index(content_id)

        try:
            self._order.remove(content_id)
            self._order.insert(curr_idx + delta, content_id)
            sm = getSiteManager()
            sm.notify(ContentChanged(self.get_content(content_id)))
        except:
            pass

    def set_order(self, order=[]):
        self._order = order

        # emit changed event for all children
        sm = getSiteManager()
        children = self.list_content()
        for child in children:
            sm.notify(ContentChanged(child))

    def __repr__(self):
        """return the ID as base representation"""

        return self.id
