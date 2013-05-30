__author__ = "David Rusk <drusk@uvic.ca>"

import unittest

import wx
from mock import Mock
from hamcrest import assert_that, equal_to

from test.base_tests import WxWidgetTestCase
from pymop.gui.controllers import ApplicationController


class ApplicationViewTest(WxWidgetTestCase):
    def setUp(self):
        self.mock_model()
        self.output_writer = Mock()
        self.name_generator = Mock()

        self.image_viewer = Mock()
        self.controller = ApplicationController(self.model, self.output_writer, self.name_generator,
                                                   self.image_viewer, unittest=True)
        self.appview = self.controller.get_view()
        self.mainframe = self.appview.mainframe
        self.mainframe_close = Mock()
        self.mainframe.Close = self.mainframe_close

    def tearDown(self):
        self.appview.close()
        self.mainframe.Destroy()

    def test_press_exit(self):
        menubar = self.mainframe.GetMenuBar()
        filemenu = menubar.GetMenu(menubar.FindMenu("File"))
        exit_button = self.get_menuitem_by_label(filemenu, "Exit")

        # Fire menu selection event
        event = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED,
                                exit_button.GetId())
        self.mainframe.ProcessEvent(event)

        assert_that(self.image_viewer.close.call_count, equal_to(1))
        assert_that(self.mainframe_close.call_count, equal_to(1))


if __name__ == '__main__':
    unittest.main()
