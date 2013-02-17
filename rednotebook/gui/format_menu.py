# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2012  Jendrik Seipp
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

import gtk

from rednotebook.gui import customwidgets


MENUITEMS_XML = '''\
    <menuitem action="Bold"/>
    <menuitem action="Italic"/>
    <menuitem action="Underline"/>
    <menuitem action="Strikethrough"/>
    <menuitem action="Clear"/>
'''

TOOLBAR_XML = '''\
<ui>
<popup action="FormatMenu">
%s
</popup>
</ui>''' % MENUITEMS_XML

MENUBAR_XML = '''\
<menu action="FormatMenuBar">
%s
</menu>
''' % MENUITEMS_XML


class FormatMenu(object):
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup()

    def setup(self):
        '''
        See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''

        uimanager = self.main_window.uimanager

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('FormatActionGroup')

        def tmpl(word):
            return word + ' (Ctrl+%s)' % word[0]

        def apply_format(action, format='bold'):
            format_to_markup = {'bold': '**', 'italic': '//', 'underline': '__',
                                'strikethrough': '--'}
            if type(action) == gtk.Action:
                format = action.get_name().lower()

            markup = format_to_markup[format]

            focus = self.main_window.main_frame.get_focus()
            iter = self.main_window.categories_tree_view.get_selected_node()

            if isinstance(focus, gtk.Entry):
                entry = focus
                pos = entry.get_position()
                # bounds can be an empty tuple
                bounds = entry.get_selection_bounds() or (pos, pos)
                selected_text = entry.get_chars(*bounds).decode('utf-8')
                entry.delete_text(*bounds)
                entry.insert_text('%s%s%s' % (markup, selected_text, markup), bounds[0])
                # Set cursor after the end of the formatted text
                entry.set_position(bounds[0] + len(markup) + len(selected_text))
            elif focus == self.main_window.categories_tree_view.tree_view and iter:
                text = self.main_window.categories_tree_view.get_iter_value(iter)
                text = '%s%s%s' % (markup, text, markup)
                self.main_window.categories_tree_view.set_iter_value(iter, text)
            elif focus == self.main_window.day_text_field.day_text_view:
                self.main_window.day_text_field.apply_format(markup)
            else:
                self.main_window.journal.show_message(_('No text or tag has been selected.'),
                                          error=True)

        def shortcut(char):
            ### Translators: The Control (Ctrl) key
            return ''  # return ' (%s+%s)' % (_('Ctrl'), char)

        # Create actions
        actions = [
            ('Bold', gtk.STOCK_BOLD, _('Bold') + shortcut('B'),
             '<Control>B', None, apply_format),
            ('Italic', gtk.STOCK_ITALIC, _('Italic') + shortcut('I'),
             '<Control>I', None, apply_format),
            ('Underline', gtk.STOCK_UNDERLINE, _('Underline') + shortcut('U'),
             '<Control>U', None, apply_format),
            ('Strikethrough', gtk.STOCK_STRIKETHROUGH, _('Strikethrough') + shortcut('K'),
             '<Control>K', None, apply_format),
            ### Translators: Clear format
            ('Clear', gtk.STOCK_CLEAR, _('Clear') + shortcut('R'),
             '<Control>R', None, self.on_clear_format),
            ### Translators: Noun
            ('FormatMenuBar', None, _('_Format')),
        ]

        actiongroup.add_actions(actions)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(TOOLBAR_XML)

        # Create a Menu
        menu = uimanager.get_widget('/FormatMenu')

        self.main_window.format_button = customwidgets.ToolbarMenuButton(gtk.STOCK_BOLD, menu)
        ### Translators: Noun
        self.main_window.format_button.set_label(_('Format'))
        tip = _('Format the selected text or tag')
        self.main_window.format_button.set_tooltip_text(tip)
        self.main_window.builder.get_object('edit_toolbar').insert(self.main_window.format_button, -1)
        self.main_window.format_actiongroup = actiongroup

    def on_clear_format(self, action):
        editor = self.main_window.day_text_field
        sel_text = editor.get_selected_text()
        for markup in ['**', '__', '//', '--', '=== ', ' ===']:
            sel_text = sel_text.replace(markup, '')
        editor.replace_selection(sel_text)
