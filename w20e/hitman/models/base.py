from persistent.mapping import PersistentMapping
from persistent import Persistent
from zope.interface import Interface
from zope.interface import implements
from datetime import datetime
from exceptions import UniqueConstraint
from BTrees.OOBTree import OOBTree
import re
from w20e.forms.formdata import FormData
from w20e.forms.xml.factory import XMLFormFactory
from w20e.forms.xml.formfile import FormFile, find_file
from w20e.hitman.utils import object_to_path


class IContent(Interface):

    """ Marker for base content """


class IFolder(IContent):

    """ Marker for folderish content """


class Base:

    """ Base content, should be extended for real content """

    def __init__(self, content_id, data_attr_name="_DATA", data=None):

        if not data:
            data = {}

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
    def content_type(self):

        return self.__class__.__name__.lower()

    @property
    def allowed_content_types(self):

        return []

    @property
    def base_id(self):

        return self.content_type

    @property
    def has_parent(self):

        return getattr(self, "__parent__", None)

    @property
    def __data__(self):

        """ Wrap data in formdata container. Keep it volatile though,
        so as not to pollute the DB. """

        try:
            return self._v_data
        except:

            data = getattr(self, self.data_attr_name)

            # migrate old hashmaps to OOBTree if necessary
            if not isinstance(data, OOBTree):
                data = OOBTree(data)
                setattr(self, self.data_attr_name, data)

            self._v_data = FormData(data=data)
            return self._v_data

    def set_attribute(self, name, value):
        """ store an attribut in a low level manner """

        data = getattr(self, self.data_attr_name)
        data[name] = value
        self._p_changed = 1
        # remove volatile cached data
        try:
            del(self._v_data)
        except:
            pass  # no worries.we didn't have the cached value

    @property
    def __form__(self):

        """ Volatile form """

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
            _root = _root.__parent__

        return _root

    @classmethod
    def defaults(self):

        return {}

    @property
    def path(self):

        """ Return path from root as list of id's"""

        return object_to_path(self, as_list=True)

    @property
    def dottedpath(self):

        """ Return path as dot separated string """

        return object_to_path(self, path_sep=".", as_list=False)


class BaseContent(Persistent, Base):

    """ Base content, should be extended for real content """

    implements(IContent)

    def __init__(self, content_id, data=None):

        if not data:
            data = {}

        Persistent.__init__(self)
        Base.__init__(self, content_id, data=data)

    def __repr__(self):
        """ return the ID as base representation """

        return self.id


class BaseFolder(PersistentMapping, Base):

    """ Base folder """

    implements(IFolder)

    def __init__(self, content_id, data=None):

        if not data:
            data = {}

        PersistentMapping.__init__(self)
        Base.__init__(self, content_id, data=data)
        self._order = []

    def add_content(self, content):

        # don't replace the content
        if content.id in self:
            raise UniqueConstraint("an item with this ID already exists at \
                    this level")

        content.__parent__ = self
        content.__name__ = content.id
        self[content.id] = content
        self._order.append(content.id)

    def rename_content(self, id_from, id_to):

        """ Move object at id_from to id_to key"""

        if id_to in self:
            raise UniqueConstraint("an item with this ID already exists at \
                    this level")

        content = self.get(id_from, None)

        if content is None:
            return False

        del self[id_from]

        content._id = id_to
        content.__name__ = id_to

        # retain order
        if id_from in self._order:
            self._order[self._order.index(id_from)] = id_to

        self[content.id] = content

    def remove_content(self, content_id):

        try:
            content = self.get(content_id, None)
            del self[content_id]
            self._order.remove(content_id)
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

    def list_content_ids(self, **kwargs):

        all_ids = self.keys()

        def _order_cmp(a, b):

            max_order = len(self._order) + 1

            return cmp(self._order.index(a) if a in self._order \
                       else max_order,
                       self._order.index(b) if b in self._order \
                                               else max_order,
                       )

        all_ids.sort(_order_cmp)

        return all_ids

    def list_content(self, content_type=None, iface=None, **kwargs):

        """ List content of this folder. If content_type is given,
        list only these things.
        """

        all_content = []

        if content_type:
            if isinstance(content_type, str):
                content_type = [content_type,]

            all_content = [obj for obj in self.values() \
                    if getattr(obj, 'content_type', None) in content_type]
        if iface:
            all_content = [obj for obj in self.values() \
                    if iface.providedBy(obj)]

        if not (content_type or iface):
            all_content = self.values()

        if kwargs.get('order_by', None):
            all_content.sort(lambda a, b: \
                             cmp(getattr(a, kwargs['order_by'], 1),
                                 getattr(b, kwargs['order_by'], 1)))
        else:
            def _order_cmp(a, b):

                max_order = len(self._order) + 1

                return cmp(self._order.index(a.id) if a.id in self._order \
                           else max_order,
                            self._order.index(b.id) if b.id in self._order \
                                                    else max_order,
                           )

            all_content.sort(_order_cmp)

        return all_content

    def find_content(self, content_type=None):

        """ Find content recursively from the given folder. Use it
        wisely... """

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
        """ change all non-letters and non-numbers to dash """

        id = str(id).lower()
        id = re.sub('[^-a-z0-9_]+', '-', id)
        return id

    def generate_content_id(self, base_id):

        base_id = self._normalize_id(base_id)

        if not base_id in self:
            return base_id

        cnt = 1

        while "%s_%s" % (base_id, cnt) in self:
            cnt += 1

        return "%s_%s" % (base_id, cnt)

    def move_content(self, content_id, delta):

        """ Move the content in the order by delta, where delta may be
        negative """

        curr_idx = self._order.index(content_id)

        try:
            self._order.remove(content_id)
            self._order.insert(curr_idx + delta, content_id)
        except:
            pass

    def set_order(self, order=[]):

        self._order = order

    def __repr__(self):
        """ return the ID as base representation """

        return self.id
