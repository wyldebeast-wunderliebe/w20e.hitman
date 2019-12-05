from builtins import str
from builtins import object
from pyramid import testing
from w20e.hitman.models.base import BaseFolder, BaseContent
import datetime
from zope.interface import Interface, implements

class ITestContent(Interface):
    """ marker interface for TestContent """
    pass


class TestContent(BaseContent):
    """ implementation of the BaseContent class just for testing """

    @implementer(ITestContent)
    edit_form = 'test_content_form.xml'


class TestBaseModel(object):

    def setup_class(self):
        self.config = testing.setUp()

        self.root = BaseFolder("root")

        self.f0 = BaseFolder("f0")
        self.f1 = BaseFolder("f1")

        self.x0 = TestContent("x0")
        self.x1 = TestContent("x1")

        self.f0.add_content(self.x0)
        self.f0.add_content(self.x1)

        self.root.add_content(self.f0)
        self.root.add_content(self.f1)

    def teardown_class(self):
        testing.tearDown()

    def test_model(self):

        request = testing.DummyRequest()

        assert ["f0", "x1"] == self.x1.path

        assert self.x0.id == 'x0'
        self.x0.set_id('x0-new')
        assert self.x0.id == 'x0-new'
        self.x0.set_id('x0')
        assert self.x0.owner == ''
        self.x0.owner = 'Tester'
        assert self.x0.owner == 'Tester'

        assert self.x0.content_type == 'testcontent'
        assert self.x0.allowed_content_types(request) == []
        assert self.x0.base_id == 'testcontent'
        assert self.x0.has_parent
        assert self.x0.__data__.as_dict() == {}
        self.x0.set_attribute('whatyouwant', 'a little respect')
        assert self.x0.__data__.as_dict() == {
                'whatyouwant': 'a little respect'}
        form = self.x0.__form__(request)
        assert self.x0.title == 'x0'
        now = datetime.datetime.now()
        assert self.x0.created <= now
        assert self.x0.changed >= self.x0.created
        assert self.x0.dottedpath == '.f0.x0'
        assert str(self.x0) == 'x0'

        gello = TestContent("gello")
        self.f0.add_content(gello)
        self.f0.rename_content("gello", "yello")
        content = self.f0.get_content("yello")
        content2 = self.f0.get_content("yello", content_type='testcontent')
        assert content == content2 == gello
        assert "yello" in self.f0._list_content_ids()
        listing1 = self.f0.list_content(content_type='testcontent')
        listing2 = self.f0.list_content(iface=ITestContent)
        listing3 = self.f0.list_content()
        assert listing1 == listing2 == listing3

        self.f0.move_content('yello', -1)
        listing4 = self.f0.list_content()
        assert listing3.index(gello) == 2
        assert listing4.index(gello) == 1

        listing_ordered = self.f0.list_content(order_by='id')
        assert listing4 != listing_ordered
        assert set(listing1) == set(listing_ordered)
        self.f0.set_order(order=[])
        assert str(self.f0) == 'f0'

        found1 = self.f0.find_content()
        found2 = self.f0.find_content(content_type="testcontent")
        assert found1
        assert found1 == found2
        assert self.f0._normalize_id("wat's up?") == "wat-s-up-"
        assert self.f0.generate_content_id("wat's up?") == "wat-s-up-"
        assert self.f0.generate_content_id("yello") == "yello_1"

        self.f0.remove_content("yello")

