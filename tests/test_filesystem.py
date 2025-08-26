import os
import unittest.mock

from rednotebook.util.filesystem import get_journal_title, _is_x11_forwarding_detected, _apply_webkit_x11_forwarding_workaround


def test_journal_title():
    root = os.path.abspath(os.sep)
    dirs = [
        ("/home/my journal", "my journal"),
        ("/my journal/", "my journal"),
        ("/home/name/Journal", "Journal"),
        ("/home/name/jörnal", "jörnal"),
        (root, root),
    ]
    for path, title in dirs:
        assert get_journal_title(path) == title


def test_x11_forwarding_detection_with_ssh_and_remote_display():
    """Test X11 forwarding detection with SSH environment and remote display."""
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CLIENT': '192.168.1.100 45678 22',
        'DISPLAY': ':10.0'
    }, clear=True):
        assert _is_x11_forwarding_detected() is True


def test_x11_forwarding_detection_with_ssh_connection_and_remote_display():
    """Test X11 forwarding detection with SSH_CONNECTION and remote display."""
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CONNECTION': '192.168.1.100 45678 192.168.1.1 22',
        'DISPLAY': ':12.0'
    }, clear=True):
        assert _is_x11_forwarding_detected() is True


def test_x11_forwarding_detection_with_ssh_tty_and_remote_display():
    """Test X11 forwarding detection with SSH_TTY and remote display."""
    with unittest.mock.patch.dict(os.environ, {
        'SSH_TTY': '/dev/pts/1',
        'DISPLAY': ':15.0'
    }, clear=True):
        assert _is_x11_forwarding_detected() is True


def test_x11_forwarding_detection_local_display_no_ssh():
    """Test that local display without SSH is not detected as X11 forwarding."""
    with unittest.mock.patch.dict(os.environ, {
        'DISPLAY': ':0.0'
    }, clear=True):
        assert _is_x11_forwarding_detected() is False


def test_x11_forwarding_detection_ssh_without_display():
    """Test that SSH without DISPLAY is not detected as X11 forwarding."""
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CLIENT': '192.168.1.100 45678 22'
    }, clear=True):
        assert _is_x11_forwarding_detected() is False


def test_x11_forwarding_detection_ssh_with_local_display():
    """Test that SSH with local display is not detected as X11 forwarding."""
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CLIENT': '192.168.1.100 45678 22',
        'DISPLAY': ':0.0'
    }, clear=True):
        assert _is_x11_forwarding_detected() is False


def test_x11_forwarding_detection_no_ssh_no_display():
    """Test that no SSH and no DISPLAY is not detected as X11 forwarding."""
    with unittest.mock.patch.dict(os.environ, {}, clear=True):
        assert _is_x11_forwarding_detected() is False


def test_x11_forwarding_detection_invalid_display():
    """Test that invalid DISPLAY format is handled gracefully."""
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CLIENT': '192.168.1.100 45678 22',
        'DISPLAY': 'invalid'
    }, clear=True):
        assert _is_x11_forwarding_detected() is False


def test_x11_forwarding_detection_malformed_display():
    """Test that malformed DISPLAY is handled gracefully."""
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CLIENT': '192.168.1.100 45678 22',
        'DISPLAY': ':abc.0'
    }, clear=True):
        assert _is_x11_forwarding_detected() is False


def test_webkit_x11_forwarding_workaround_sets_environment_variables():
    """Test that webkit workaround sets environment variables when X11 forwarding is detected."""
    expected_vars = {
        'WEBKIT_DISABLE_SANDBOX': '1',
        'WEBKIT_DISABLE_DMABUF_RENDERER': '1',  
        'WEBKIT_DISABLE_COMPOSITING_MODE': '1'
    }
    
    # Start with clean environment
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CLIENT': '192.168.1.100 45678 22',
        'DISPLAY': ':10.0'
    }, clear=True):
        _apply_webkit_x11_forwarding_workaround()
        
        # Check that all expected variables are set
        for var, value in expected_vars.items():
            assert os.environ.get(var) == value


def test_webkit_x11_forwarding_workaround_no_ssh():
    """Test that webkit workaround does not set variables when X11 forwarding is not detected."""
    webkit_vars = [
        'WEBKIT_DISABLE_SANDBOX',
        'WEBKIT_DISABLE_DMABUF_RENDERER', 
        'WEBKIT_DISABLE_COMPOSITING_MODE'
    ]
    
    # Local environment (no SSH)
    with unittest.mock.patch.dict(os.environ, {
        'DISPLAY': ':0.0'
    }, clear=True):
        _apply_webkit_x11_forwarding_workaround()
        
        # Check that webkit variables are not set
        for var in webkit_vars:
            assert var not in os.environ


def test_webkit_x11_forwarding_workaround_preserves_existing_variables():
    """Test that webkit workaround does not override existing environment variables."""
    # Start with some preset values
    with unittest.mock.patch.dict(os.environ, {
        'SSH_CLIENT': '192.168.1.100 45678 22',
        'DISPLAY': ':10.0',
        'WEBKIT_DISABLE_SANDBOX': 'custom_value'
    }, clear=True):
        _apply_webkit_x11_forwarding_workaround()
        
        # Check that existing value is preserved
        assert os.environ.get('WEBKIT_DISABLE_SANDBOX') == 'custom_value'
        
        # Check that other variables are still set
        assert os.environ.get('WEBKIT_DISABLE_DMABUF_RENDERER') == '1'
        assert os.environ.get('WEBKIT_DISABLE_COMPOSITING_MODE') == '1'
