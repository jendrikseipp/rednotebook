#-----------------------------------------------------------------------------
# Copyright (c) 2005-2018, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # PyGObject modules loaded through the gi repository are marked as
    # MissingModules by modulegraph so we convert them to
    # RuntimeModules so their hooks are loaded and run.
    api.add_runtime_module(api.module_name)
