def pytest_configure(config):
    import builtins
    import sys
    from unittest.mock import MagicMock, patch
    
    # Mock command line arguments to avoid parsing issues during imports
    with patch('sys.argv', ['test']):
        pass

    # Mock GTK and related modules for testing
    class MockGI:
        class Repository:
            GLib = MagicMock()
            Gtk = MagicMock()
            GIRepository = MagicMock()
            GObject = MagicMock()
            Pango = MagicMock()
            Gio = MagicMock()
            Gdk = MagicMock()
            GdkPixbuf = MagicMock()
            GtkSource = MagicMock()
        
        repository = Repository()
        
        @staticmethod
        def require_version(name, version):
            pass
    
    # Mock the gi module and its components
    sys.modules['gi'] = MockGI()
    sys.modules['gi.repository'] = MockGI.Repository()
    sys.modules['gi.repository.GLib'] = MockGI.Repository.GLib
    sys.modules['gi.repository.Gtk'] = MockGI.Repository.Gtk
    sys.modules['gi.repository.GIRepository'] = MockGI.Repository.GIRepository
    sys.modules['gi.repository.GObject'] = MockGI.Repository.GObject
    sys.modules['gi.repository.Pango'] = MockGI.Repository.Pango
    sys.modules['gi.repository.Gio'] = MockGI.Repository.Gio
    sys.modules['gi.repository.Gdk'] = MockGI.Repository.Gdk
    sys.modules['gi.repository.GdkPixbuf'] = MockGI.Repository.GdkPixbuf
    sys.modules['gi.repository.GtkSource'] = MockGI.Repository.GtkSource

    if not hasattr(builtins, "_"):
        builtins._ = lambda x: x
