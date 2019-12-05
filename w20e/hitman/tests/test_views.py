# -*- coding: utf-8 -*- 
from builtins import object
from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from w20e.hitman.models.base import BaseFolder, BaseContent
from w20e.hitman.views import base
from w20e.hitman.models import Registry
import datetime

class TestContent(BaseContent):
    """ implementation of the BaseContent class just for testing """

    edit_form = 'test_content_form.xml'


class TestUtils(object):

    def setup_class(self):
        self.config = testing.setUp()

        self.root = BaseFolder("root")
        self.root.__name__ = 'root'

        self.f0 = BaseFolder("f0")
        self.f1 = BaseFolder("f1")

        self.x0 = TestContent("x0")
        self.x1 = TestContent("x1")

        self.f0.add_content(self.x0)
        self.f0.add_content(self.x1)

        self.root.add_content(self.f0)
        self.root.add_content(self.f1)

        Registry.register('testcontent', TestContent)

    def teardown_class(self):
        testing.tearDown()

    def test_view_changed(self):

        request = testing.DummyRequest()
        view = base.ContentView(self.x0, request)
        now = datetime.datetime.now()
        assert self.x0.changed <= now
        assert view.changed == self.x0.changed.strftime("%d-%m-%Y %H:%M")

    def test_view_list_fields(self):

        request = testing.DummyRequest()
        view = base.ContentView(self.x0, request)
        fields = view.list_fields()

        labels = set(["Name", "Short description", "Keywords",
            "Page text (including images)"])
        field_labels = set([f['label'] for f in fields])
        assert labels ^ field_labels == set([])

    def test_DelView(self):

        request = testing.DummyRequest()
        request.application_url = 'http://example.com/'

        assert 'x1' in self.f0._list_content_ids()

        view = base.DelView(self.x1, request)

        result = view()
        assert result == {}
        assert 'x1' in self.f0._list_content_ids()

        request.params['cancel'] = 'cancel'
        result = view()
        assert isinstance(result, HTTPFound)
        assert result.location == 'http://example.com/root/f0/x1/'
        assert 'x1' in self.f0._list_content_ids()

        request.params['submit'] = 'submit'
        result = view()
        assert isinstance(result, HTTPFound)
        after_del_redirect = view.after_del_redirect
        assert result.location == after_del_redirect

        # check if the object has been removed
        assert 'x1' not in self.f0._list_content_ids()

    def test_EditView(self):

        request = testing.DummyRequest()
        request.application_url = 'http://example.com/'

        view = base.EditView(self.x0, request)

        assert view.content_type == 'testcontent'
        assert view.after_edit_redirect == 'http://example.com/root/f0/x0/'

        assert self.x0.__data__['name'] is None

        # submit empty edit form, will result in error (name is required)
        request.params['w20e.forms.process'] = 1
        result = view()
        assert isinstance(result, dict)
        assert 'name' in result['errors']
        assert 'required' in result['errors']['name']
        assert self.x0.__data__['name'] is None

        # submit form with name
        name = "Gëllo, I'm x0"
        request.params['name'] = name
        view = base.EditView(self.x0, request)
        result = view()
        assert isinstance(result, HTTPFound)
        assert result.location == 'http://example.com/root/f0/x0/'
        assert self.x0.__data__['name'] == name

    def test_AddView(self):

        request = testing.DummyRequest()
        request.application_url = 'http://example.com/'
        request.params['ctype'] = 'testcontent'

        view = base.AddView(self.f1, request)
        assert view.content_type == 'testcontent'
        assert view.after_add_redirect == 'http://example.com/root/f1/'
        assert view.cancel_add_redirect == 'http://example.com/root/f1/'

        result = view()
        assert isinstance(result, dict)
        assert result['status'] == 'unknown'
        assert result['errors'] == {}

        # submit empty form
        request.params['w20e.forms.process'] = 1
        view = base.AddView(self.f1, request)
        result = view()
        assert isinstance(result, dict)
        assert result['status'] == 'error'
        assert 'name' in result['errors']
        assert 'required' in result['errors']['name']

        # submit form with name set
        name = "My ådded cøntënt"
        request.params['w20e.forms.process'] = 1
        request.params['name'] = name
        view = base.AddView(self.f1, request)
        result = view()
        assert isinstance(result, HTTPFound)
        assert result.location == 'http://example.com/root/f1/'
        content = self.f1.list_content(content_type='testcontent')
        assert len(content) == 1
        assert content[0].__data__['name'] == name
