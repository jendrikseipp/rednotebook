# RedNotebook - Desktop Journal

RedNotebook is a desktop journal application written in Python using GTK3, GtkSourceView and WebKitGTK. It allows users to format, tag, and search journal entries with support for pictures, links, templates, spell checking and export to multiple formats.

**ALWAYS follow these instructions first and only fallback to additional search and context gathering if the information here is incomplete or found to be in error.**

## Working Effectively

### Bootstrap and Install Dependencies
```bash
# Install system dependencies (takes ~3 minutes, NEVER CANCEL)
sudo apt-get update
sudo apt-get -y install -qq gettext gir1.2-gdkpixbuf-2.0 gir1.2-glib-2.0 gir1.2-gtk-3.0 gir1.2-gtksource-4 gir1.2-pango-1.0 gir1.2-webkit2-4.1 python3 python3-enchant python3-gi python3-setuptools python3-yaml tox python3-flake8

# Install testing framework (if pip network access available)
pip install pytest
```

**CRITICAL TIMING**: Dependency installation takes approximately 3 minutes. NEVER CANCEL this process. Set timeout to 300+ seconds.

### Run the Application
```bash
# Start RedNotebook directly (preferred method, <5 seconds)
./run

# Alternative: Run with Python directly
python3 rednotebook/journal.py

# Get help and verify installation
./run --help
./run --version

# Run with virtual display for headless environments
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
./run --version
```

**NOTE**: RedNotebook requires a graphical environment (GTK3). Use Xvfb for headless testing. Application startup is very fast (<5 seconds).

### Development Scripts and Testing

```bash
# Run main test environment (includes pytest + extra scripts from tox.ini)
tox -e py
```

**TIMING**: All development scripts execute quickly. These are safe to run frequently.

## Linting and Code Quality

### Pre-commit Hooks Setup
```bash
# Install and set up pre-commit hooks
pip install pre-commit  # May timeout due to network issues
pre-commit install
```

### Manual Linting (Validated to Work)
```bash
# Run flake8 linting (~0.4 seconds, RECOMMENDED)
python3 -m flake8 --extend-ignore=E203,E402,F821 --max-line-length=110 --builtins="_" --exclude=rednotebook/external/ rednotebook/

# Check style on specific files
python3 -m flake8 --extend-ignore=E203,E402,F821 --max-line-length=110 path/to/file.py
```

**TIMING**: Linting is very fast (~0.4 seconds). The codebase is clean and should pass without errors.

## Testing Strategy

### Known Testing Limitations
- **tox may fail** due to network connectivity issues with PyPI
- **Direct pytest import fails** due to command-line argument parsing in main module
- **pip install may timeout** in network-restricted environments

### Workarounds for Testing
```bash
# Test core functionality without pytest
python3 -c "import sys; sys.path.insert(0, '.'); import rednotebook.util.utils; print('Utils import: OK')"

# Test GTK imports
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('GTK3: OK')"

# Run application smoke test
timeout 10 ./run --help >/dev/null && echo "Application: OK"

# Manual validation of changes (ALWAYS DO THIS)
export DISPLAY=:99
timeout 5 ./run --version
```

### If tox Works (Network Dependent)
```bash
# Run style checks (may take 30+ seconds, NEVER CANCEL)
tox -v -e style

# Run Python tests (may take 60+ seconds, NEVER CANCEL)
tox -v -e py
```

**CRITICAL**: If tox commands work, they may take 30-60 seconds. NEVER CANCEL these operations.

## Validation Requirements

### Manual Testing Scenarios
After making any changes, ALWAYS test the following scenarios:

1. **Application Startup**: `./run --version` should complete without errors
2. **Help Display**: `./run --help` should show proper usage information
3. **Core Import**: Verify core modules can be imported without issues
4. **Linting**: Code should pass flake8 without errors (excluding external/)

### Before Committing Changes
```bash
# ALWAYS run linting before committing
python3 -m flake8 --extend-ignore=E203,E402,F821 --max-line-length=110 --builtins="_" --exclude=rednotebook/external/ rednotebook/

# Verify application still starts
./run --version

# Build translations if you modified po files
python3 dev/build_translations.py test-translations
```

## Common Tasks and File Locations

### Key Files and Directories
```bash
# Main application entry point
rednotebook/journal.py

# Core application modules
rednotebook/
├── gui/              # GTK user interface components
├── util/             # Utility functions and helpers
├── external/         # Third-party code (DO NOT LINT)
├── storage.py        # Data storage and journal management
├── configuration.py  # Settings and configuration
└── info.py          # Version and application metadata

# Configuration and build
setup.py              # Python package setup
pyproject.toml        # Build configuration and tool settings
tox.ini               # Testing environment configuration
.pre-commit-config.yaml # Pre-commit hook configuration

# Development tools
dev/
├── build_translations.py  # Translation building script
├── whitelist.py           # Code validation script
└── generate-help.py       # Documentation generator

# Platform-specific
win/                   # Windows build scripts and spec files
web/                   # Website build scripts
```

### Frequently Modified Files
- `rednotebook/gui/` - UI components and dialogs
- `rednotebook/util/` - Utility functions and helpers
- `rednotebook/storage.py` - Journal data handling
- `tests/` - Test files (when testing works)

### Build Artifacts (DO NOT COMMIT)
- `.tox/` - Testing environments
- `test-translations/` - Built translation files
- `__pycache__/` - Python bytecode
- `.pytest_cache/` - Test cache files

## Troubleshooting

### Network Connectivity Issues
- **pip timeouts**: Use system packages (`apt-get install python3-package`) instead
- **tox failures**: Run individual commands manually
- **pre-commit install fails**: Install linting tools via apt

### Application Won't Start
- Verify GTK3 dependencies are installed
- Check that Python 3.8+ is available
- For headless environments, ensure Xvfb is running with DISPLAY set

### Import Errors
- Ensure you're in the repository root directory
- Add current directory to Python path: `sys.path.insert(0, '.')`
- Verify all system dependencies are installed

### Testing Issues
- **pytest import failures**: Use manual import tests instead
- **tox hangs**: May be network-related, use manual commands
- **CI failures**: Ensure linting passes locally first

## Important Notes

- **NEVER CANCEL** long-running operations (dependency installs, builds)
- **ALWAYS TEST** application startup after making changes
- **ALWAYS RUN** linting before committing changes
- **Network issues** are common - have manual workarounds ready
- **External code** in `rednotebook/external/` should not be modified or linted
- **Virtual display** required for headless environments (use Xvfb)

This desktop application successfully runs in containerized environments with proper GTK3 setup and virtual display configuration.
