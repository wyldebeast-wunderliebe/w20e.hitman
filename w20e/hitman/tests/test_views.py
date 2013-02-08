from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from w20e.hitman.models.base import BaseFolder, BaseContent
from w20e.hitman.views import base
from w20e.forms.xml.factory import XMLFormFactory
import os
import datetime


class TestUtils:

    def setup_class(self):
        self.config = testing.setUp()

        #create simple w20e.form forms
        filename = "test_content_form.xml"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath) as f:
            data = f.read()
            xmlff = XMLFormFactory(data)
            self.test_content_form = xmlff.create_form(action="")

        self.root = BaseFolder("root")
        self.root.__name__ = 'root'

        self.f0 = BaseFolder("f0")
        self.f1 = BaseFolder("f1")

        self.x0 = BaseContent("x0")
        self.x0._v_form = self.test_content_form

        self.x1 = BaseContent("x1")
        self.x1._v_form = self.test_content_form

        self.f0.add_content(self.x0)
        self.f0.add_content(self.x1)

        self.root.add_content(self.f0)
        self.root.add_content(self.f1)

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

    def test_view_delete(self):

        request = testing.DummyRequest()
        request.application_url = 'http://example.com/'

        view = base.DelView(self.x1, request)

        result = view()
        assert result == {}

        request.params['cancel'] = 'cancel'
        result = view()
        assert isinstance(result, HTTPFound)
        assert result.location == 'http://example.com/root/f0/x1/'

        request.params['submit'] = 'submit'
        result = view()
        assert isinstance(result, HTTPFound)
        after_del_redirect = view.after_del_redirect
        assert result.location == after_del_redirect
