from persistent.mapping import PersistentMapping
from persistent import Persistent
from zope.interface import Interface
from zope.interface import implements
from datetime import datetime
from exceptions import UniqueConstraint
import re
from w20e.hitman.events import ContentRemoved, ContentAdded, ContentChanged
from w20e.forms.formdata import FormData


class IContent(Interface):

    """ Marker for base content """


class IFolder(IContent):

    """ Marker for folderish content """


class Base:

    """ Base content, should be extended for real content """

    def __init__(self, content_id, data_attr_name="_DATA", data={}):

        self._id = content_id
        self.data_attr_name = data_attr_name
        setattr(self, data_attr_name, data)
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
            self._v_data = FormData(data=getattr(self, self.data_attr_name))
            return self._v_data

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

        while getattr(_root, "__parent__", None):
            _root = _root.__parent__

        return _root

    @classmethod
    def defaults(self):

        return {}


class BaseContent(Persistent, Base):

    """ Base content, should be extended for real content """

    implements(IContent)

    def __init__(self, content_id, data={}):

        Persistent.__init__(self)
        Base.__init__(self, content_id, data=data)


class BaseFolder(PersistentMapping, Base):

    """ Base folder """

    implements(IFolder)

    def __init__(self, content_id, data={}):

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


    def remove_content(self, content_id):

        try:
            del self[content_id]
            self._order.remove(content_id)
        except:
            pass


    def get_content(self, content_id, content_type=None):

        obj = self.get(content_id, None)

        if content_type:

            if getattr(obj, "content_type", None) == content_type:

                return obj

            else:

                return None

        return obj


    def list_content(self, content_type=None, **kwargs):

        """ List content of this folder. If content_type is given,
        list only these things.
        """

        all_content = []

        # start with order on self._order if it's there...
        for content_id in self._order:
            if self.has_key(content_id):
                all_content.append(self[content_id])
        all_content += [content for content in self.values() if not content.id in self._order]

        if content_type:
            all_content = [obj for obj in all_content if getattr(obj,\
                     'content_type', None) == content_type]

        if kwargs.get('order_by', None):
            all_content.sort(lambda a, b: \
                    cmp(getattr(a, kwargs['order_by'], 1),
                        getattr(b, kwargs['order_by'], 1)))

        return all_content

    
    def find_content(self, content_type=None):

        """ Find content recursively from the given folder. Use it
        wisely... """

        found = self.list_content(content_type=content_type)

        for sub in self.list_content():

            try:
                found += sub.find_content(content_type= content_type)
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

        if not self.get_content(base_id):
            return self._normalize_id(base_id)

        cnt = 1

        while self.get_content("%s_%s" % (base_id, cnt)):

            cnt += 1

        return self._normalize_id("%s_%s" % (base_id, cnt))


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
