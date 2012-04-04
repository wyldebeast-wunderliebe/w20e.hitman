from pyramid.httpexceptions import HTTPFound
from w20e.hitman.models import Registry
from w20e.forms.pyramid.formview import formview as pyramidformview
from w20e.forms.pyramid.formview import xmlformview as pyramidxmlformview
from w20e.forms.xml.formfile import FormFile, find_file
from w20e.forms.form import FormValidationError
from pyramid.url import resource_url
from datetime import datetime
from ..events import ContentRemoved, ContentAdded, ContentChanged


class BaseView(object):

    """ Helper class for finding parents, URL's, etc. """

    def __init__(self, context, request):

        self.context = context
        self.request = request

    @property
    def parent_url(self):

        return resource_url(self.context.__parent__, self.request)

    @property
    def url(self):

        return resource_url(self.context, self.request)

    @property
    def allowed_content_types(self):

        return self.context.allowed_content_types

    @property
    def has_parent(self):

        return self.context.has_parent

    def list_content(self, **kwargs):

        try:
            return self.context.list_content(**kwargs)
        except:
            return []

    @property
    def content_type(self):

        return self.context.content_type

    @property
    def title(self):

        return self.context.title

    def __call__(self):

        return {}

    @property
    def created(self):

        return self.context.created.strftime("%d-%m-%Y %H:%M")


class ContentView(BaseView, pyramidformview):

    """ Helper class for finding parents, URL's, etc. """

    def __init__(self, context, request, form=None):

        BaseView.__init__(self, context, request)
        pyramidformview.__init__(self, context, request, context.__form__)

    @property
    def changed(self):

        return self.context.changed.strftime("%d-%m-%Y %H:%M")

    def list_fields(self):

        """ Return fields as dict {name, lexical value} """

        fields = []

        for field in self.form.data.getFields():

            val = self.form.getFieldValue(field, lexical=True)
            raw = self.form.getFieldValue(field, lexical=False)
            label = None
            renderable = self.form.view.getRenderableByBind(field)

            if renderable:
                label = renderable.label

            if label:
                fields.append({'label': label,
                               'value': val,
                               'type': renderable.type,
                               'raw': raw})

        return fields


class DelView(BaseView):

    @property
    def after_del_redirect(self):

        """ Where to go after successfull delete?"""

        return self.parent_url

    def __call__(self):

        if self.request.params.get("submit", None):

            content = self.context
            parent = self.context.__parent__

            parent.remove_content(self.context.id)

            self.request.registry.notify(ContentRemoved(content, parent))
            return HTTPFound(location=self.after_del_redirect)
        elif self.request.params.get("cancel", None):
            return HTTPFound(location=self.url)

        return {}


class EditView(ContentView):

    """ Generic edit form """

    @property
    def content_type(self):

        return self.context.content_type

    @property
    def after_edit_redirect(self):

        """ Where to go after successfull edit?"""

        return self.url

    def __call__(self):

        res = pyramidformview.__call__(self)

        if res.get('status', None) == "cancelled":
            return HTTPFound(location=self.url)
        elif res.get('status', None) == "stored":

            self.context._changed = datetime.now()
            try:
                delattr(self.context, "_v_data")
            except:
                pass
            self.request.registry.notify(ContentChanged(self.context))

            return res
        else:
            return res


class AddView(BaseView, pyramidxmlformview):

    """ add form for base content """

    def __init__(self, context, request):

        BaseView.__init__(self, context, request)

        ctype = request.params.get("ctype", None)

        clazz = Registry.get(ctype)

        add_form = find_file(clazz.add_form, clazz)

        if clazz:
            pyramidxmlformview.__init__(self, context, request,
                                     FormFile(add_form),
                                     retrieve_data=False)

        self.ctype = ctype
        self.clazz = clazz

    @property
    def content_type(self):

        return self.ctype

    @property
    def after_add_redirect(self):

        """ Where to go after successfull add?"""

        return self.url

    @property
    def cancel_add_redirect(self):

        """ Where to go after cancelled add?"""

        return self.url

    def __call__(self):

        if not self.ctype or not self.clazz:
            return HTTPFound(location=self.url)

        form = self.form
        res = {'status': 'called', 'errors': {}}

        if self.request.params.get("cancel", None):
            return HTTPFound(location=self.cancel_add_redirect)

        if self.request.params.get("submit", None):

            self._process_data(form, form.view, self.request.params)
            res['status'] = 'processed'

            try:
                form.validate()

            except FormValidationError, fve:
                res['errors'] = fve.errors
                res['status'] = 'error'

        if res['status'] == "processed":

            content = self.clazz("_TMP")

            form.submission.submit(form, content, self.request)
            res['status'] = 'stored'

            content_id = self.context.generate_content_id(content.base_id)
            content.set_id(content_id)

            self.context.add_content(content)
            res['object'] = content

            self.request.registry.notify(ContentAdded(content, self.context))

            return HTTPFound(location=self.after_add_redirect)

        return res
