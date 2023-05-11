# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
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

from rednotebook.util.filesystem import WebKit2


MAX_HITS = 10**6


if WebKit2:

    class Browser(WebKit2.WebView):
        def __init__(self):
            WebKit2.WebView.__init__(self)
            webkit_settings = self.get_settings()
            webkit_settings.set_property("enable-plugins", False)

        def load_html(self, html):
            WebKit2.WebView.load_html(self, content=html, base_uri="file:///")

    class HtmlView(Browser):
        def __init__(self):
            Browser.__init__(self)
            self.search_text = ""
            self.connect("load-changed", self.on_load_changed)
            self.show_all()

        def set_font_size(self, size):
            zoom = 1.0 if size <= 0 else size / 10.0
            # It seems webkit shows text a little bit bigger.
            zoom *= 0.90
            self.set_zoom_level(zoom)

        def highlight(self, search_text):
            # Tell the webview which text to highlight after the html is loaded
            self.search_text = search_text
            self.get_find_controller().search(
                self.search_text, WebKit2.FindOptions.CASE_INSENSITIVE, MAX_HITS
            )

        def on_load_changed(self, webview, event):
            """
            We use this method to highlight searched text.
            Whenever new searched text is entered it is saved in the HtmlView
            instance and highlighted, when the html is loaded.

            Trying to highlight text while the page is still being loaded
            does not work.
            """
            if event == WebKit2.LoadEvent.FINISHED:
                if self.search_text:
                    self.highlight(self.search_text)
                else:
                    webview.get_find_controller().search_finish()
