import unittest
from pyramid import testing
from w20e.hitman.models.base import BaseFolder, BaseContent
from w20e.hitman.utils import object_to_path, path_to_object


class UtilsTest(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        self.root = BaseFolder("root")

        self.f0 = BaseFolder("f0")
        self.f1 = BaseFolder("f1")

        self.x0 = BaseContent("x0")
        self.x1 = BaseContent("x1")

        self.f0.add_content(self.x0)
        self.f0.add_content(self.x1)

        self.root.add_content(self.f0)
        self.root.add_content(self.f1)

    def tearDown(self):
        testing.tearDown()

    def test_object_to_path(self):

        self.assertEquals(["f0", "x1"], object_to_path(self.x1, as_list=True))
        self.assertEquals("/f0/x1", object_to_path(self.x1))
        self.assertEquals(".f0.x1", object_to_path(self.x1, path_sep="."))

    def test_path_to_object(self):

        self.assertEquals(self.x0, path_to_object("/f0/x0", self.root))
