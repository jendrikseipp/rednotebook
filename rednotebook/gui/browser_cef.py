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
import sys

from gi.repository import Gdk, GObject, Gtk

from rednotebook.util import filesystem


_cls = None


def get_html_view_class():
    global _cls
    if not filesystem.IS_WIN:
        return None
    if not _cls:
        _cls = _make_html_view_class()
    return _cls


def _make_html_view_class():
    try:
        from cefpython3 import cefpython as cef
    except ImportError as err:
        logging.info(
            "CEF Python not found. Disabling clouds and"
            ' in-app previews. Error message: "{}"'.format(err)
        )
        return None

    class HtmlView(Gtk.DrawingArea):
        """
        Loading HTML strings only works if we pass the `url` parameter to
        CreateBrowserSync.

        When we call load_html() the first time, the browser is not yet
        created. Therefore, we store the initial html and load it when
        the browser is created.

        """

        NOTEBOOK_URL = "file:///"

        def __init__(self):
            super().__init__()
            self._browser = None
            self._win32_handle = None
            self._initial_html = ""

            sys.excepthook = cef.ExceptHook  # To shutdown CEF processes on error.
            cef.Initialize(settings={"context_menu": {"enabled": False}})

            GObject.threads_init()
            GObject.timeout_add(10, self.on_timer)

            self.connect("configure-event", self.on_configure)
            self.connect("size-allocate", self.on_size_allocate)
            self.connect("focus-in-event", self.on_focus_in)
            self.connect("realize", self.on_realize)

        def load_html(self, html):
            if self._browser:
                self._browser.GetMainFrame().LoadString(html, self.NOTEBOOK_URL)
            else:
                self._initial_html = html

        def set_font_size(self, size):
            pass

        def get_handle(self):
            Gdk.threads_enter()
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
            gpointer = ctypes.pythonapi.PyCapsule_GetPointer(
                self.get_property("window").__gpointer__, None
            )
            # The GTK 3.22 stack needs "gdk-3-3.0.dll".
            libgdk = ctypes.CDLL("libgdk-3-0.dll")
            handle = libgdk.gdk_win32_window_get_handle(gpointer)
            Gdk.threads_leave()
            return handle

        def on_timer(self):
            cef.MessageLoopWork()
            return True

        def on_realize(self, *_):
            self._embed_browser()

        def _embed_browser(self):
            window_info = cef.WindowInfo()
            self._win32_handle = self.get_handle()
            window_info.SetAsChild(self._win32_handle)
            self._browser = cef.CreateBrowserSync(window_info, url=self.NOTEBOOK_URL)
            self._browser.SetClientCallback("OnBeforeBrowse", self.on_before_browse)
            self._browser.SetClientCallback("OnAddressChange", self.on_address_change)
            self.load_html(self._initial_html)
            self._initial_html = None

        @GObject.Signal(name="on-url-clicked", arg_types=(str,))
        def url_clicked_signal(self, url):
            logging.debug("Emitting on-url-clicked signal: %s", url)

        def on_before_browse(self, browser, frame, request, **_):
            url = request.GetUrl()
            # For some reason GetUrl() appends slash to the returned URL so we need to compensate for it:
            # (https://bugs.chromium.org/p/chromium/issues/detail?id=339054 might be the cause)
            if url == self.NOTEBOOK_URL + "/":
                # On first invocation the url points to dummy NOTEBOOK_URL.
                # There is no reason to emit signal for it.
                return False
            self.url_clicked_signal.emit(url)
            return True

        def on_address_change(self, browser, frame, url):
            if url == self.NOTEBOOK_URL:
                return
            self.url_clicked_signal.emit(url)

        def on_configure(self, *_):
            if self._browser:
                self._browser.NotifyMoveOrResizeStarted()
            return False

        def on_size_allocate(self, _, data):
            if self._browser:
                cef.WindowUtils().OnSize(self._win32_handle, 0, 0, 0)

        def on_focus_in(self, *_):
            if self._browser:
                self._browser.SetFocus(True)
                return True
            return False

        def shutdown(self, *_):
            if self._browser:
                self._browser.CloseBrowser(True)
                # Clear browser references that you keep anywhere in your
                # code. All references must be cleared for CEF to shutdown cleanly.
                self._browser = None
            cef.Shutdown()

    return HtmlView
