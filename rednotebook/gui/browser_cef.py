# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2018  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import ctypes
import logging
import os
import sys
import webbrowser

from gi.repository import Gtk, GObject, Gdk

from rednotebook.util import filesystem

try:
    from cefpython3 import cefpython as cef
except ImportError as err:
    cef = None
    if filesystem.IS_WIN:
        logging.info(
            'CEF Python not found. Disabling clouds and'
            ' in-app previews. Error message: "{}"'.format(err))


if cef:
    class RequestHandler:
        def OnBeforeBrowse(self, browser, frame, request, **_):
            """Called when the loading state has changed."""
            print("REQUEST", browser, request)
            webbrowser.open(request.GetUrl())
            # Cancel request.
            return True


    class HtmlView(Gtk.DrawingArea):
        """
        Loading HTML strings only works if we pass the `url` parameter to
        CreateBrowserSync.

        When we call load_html() the first time, the browser is not yet
        created. Therefore, we store the initial html and load it when
        the browser is created.

        TODO: Clean shutdown.
        TODO: Remove debug output.

        """
        def __init__(self):
            super().__init__()
            self.browser = None
            self.win32_handle = None
            self.initial_html = ''

            sys.excepthook = cef.ExceptHook  # To shutdown CEF processes on error.
            cef.Initialize(settings={"context_menu": {"enabled": False}})

            GObject.threads_init()
            GObject.timeout_add(10, self.on_timer)
            self.on_startup()
            #self.connect("shutdown", self.on_shutdown)

        def load_html(self, html):
            print("LOAD")
            if self.browser:
                print("HTML")
                self.browser.GetMainFrame().LoadString(html, "http://dummy/")
            else:
                self.initial_html = html

        def set_font_size(self, size):
            pass

        def get_handle(self):
            Gdk.threads_enter()
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
            gpointer = ctypes.pythonapi.PyCapsule_GetPointer(
                self.get_property("window").__gpointer__, None)
            libgdk = ctypes.CDLL("libgdk-3-0.dll")
            self.win32_handle = libgdk.gdk_win32_window_get_handle(gpointer)
            Gdk.threads_leave()
            return self.win32_handle

        def on_timer(self):
            cef.MessageLoopWork()
            return True

        def on_startup(self, *_):
            self.connect("configure-event", self.on_configure)
            self.connect("size-allocate", self.on_size_allocate)
            self.connect("focus-in-event", self.on_focus_in)
            self.connect("delete-event", self.on_window_close)
            self.connect("realize", self.on_activate)

            self.connect("draw", self.on_draw)
            self.connect("realize", self.on_realize)

        def on_draw(self, *_):
            print("DRAW")

        def on_realize(self, *_):
            print("REALIZE")

        def on_activate(self, *_):
            print("ACTIVATE")
            self.embed_browser()

        def embed_browser(self):
            window_info = cef.WindowInfo()
            window_info.SetAsChild(self.get_handle())
            self.browser = cef.CreateBrowserSync(
                window_info,
                url="file://dummy",
            )
            self.browser.SetClientHandler(RequestHandler())
            self.load_html(self.initial_html)
            self.initial_html = None

        def on_configure(self, *_):
            print("CONFIGURE")
            if self.browser:
                self.browser.NotifyMoveOrResizeStarted()
            return False

        def on_size_allocate(self, _, data):
            print("ALLOCATE")
            if self.browser:
                cef.WindowUtils().OnSize(self.win32_handle, 0, 0, 0)

        def on_focus_in(self, *_):
            if self.browser:
                self.browser.SetFocus(True)
                return True
            return False

        def on_window_close(self, *_):
            print("WINDOW CLOSE")
            if self.browser:
                self.browser.CloseBrowser(True)
                self.clear_browser_references()

        def clear_browser_references(self):
            # Clear browser references that you keep anywhere in your
            # code. All references must be cleared for CEF to shutdown cleanly.
            self.browser = None

        def on_shutdown(self, *_):
            cef.Shutdown()
