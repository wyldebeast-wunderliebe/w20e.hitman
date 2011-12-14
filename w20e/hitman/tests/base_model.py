import unittest
from pyramid import testing
from w20e.hitman.models.base import BaseFolder, BaseContent


class BaseModelTest(unittest.TestCase):

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

    def test_paths(self):

        self.assertEquals(["f0", "x1"], self.x1.path)
