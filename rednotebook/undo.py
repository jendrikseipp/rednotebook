# -*- coding: utf-8 -*-
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

from collections import defaultdict


class Action(object):
    def __init__(self, undo_function, redo_function):
        self.undo_function = undo_function
        self.redo_function = redo_function


class UndoRedoManager(object):
    SIZE = 100
    BUFFER = 20

    def __init__(self, main_window):
        self.main_window = main_window

        self.undo_action = self.main_window.uimanager.get_widget('/MainMenuBar/Edit/Undo').get_action()
        self.redo_action = self.main_window.uimanager.get_widget('/MainMenuBar/Edit/Redo').get_action()

        self.undo_stacks = defaultdict(list)
        self.redo_stacks = defaultdict(list)

        # Unique identifier for undo stacks. Can be a date or a template name.
        self.current_stack = None

    @property
    def undo_stack(self):
        assert self.current_stack is not None
        return self.undo_stacks[self.current_stack]

    @property
    def redo_stack(self):
        assert self.current_stack is not None
        return self.redo_stacks[self.current_stack]

    def set_stack(self, stack):
        self.current_stack = stack
        self.update_buttons()

    def add_action(self, action):
        self.undo_stack.append(action)

        # Delete some items, if the undo stack grows too big.
        if len(self.undo_stack) > self.SIZE + self.BUFFER:
            del self.undo_stack[:self.BUFFER]

        # When a new action has been made, forget all redos.
        del self.redo_stack[:]

        self.update_buttons()

    def undo(self, *args):
        assert self.can_undo()

        action = self.undo_stack.pop()
        action.undo_function()
        self.redo_stack.append(action)

        self.update_buttons()

    def redo(self, *args):
        assert self.can_redo()

        action = self.redo_stack.pop()
        action.redo_function()
        self.undo_stack.append(action)

        self.update_buttons()

    def can_undo(self):
        return bool(self.undo_stack)

    def can_redo(self):
        return bool(self.redo_stack)

    def update_buttons(self):
        self.undo_action.set_sensitive(self.can_undo())
        self.redo_action.set_sensitive(self.can_redo())
