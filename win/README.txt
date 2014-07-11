The following instructions have not been tested. Please report if they
work or don't.

Windows
=======

    # Install dependencies.
    C:\\Python27\python.exe create-build-env.py

    # Run.
    C:\\Python27\python.exe rednotebook\journal.py


Linux
=====

    BUILD_ENV_TARBALL=/tmp/rn-build-env.tar.gz
    BUILD_ENV=/tmp/rn-build-env

    # Install all dependencies in a wine environment and zip it.
    ./create-build-env.py $BUILD_ENV_TARBALL

    # Unzip tarball to create build environment and build windows
    # executable in it.
    ./cross-compile-exe.py $BUILD_ENV_TARBALL $BUILD_ENV

    # Build windows installer for version 1.8.0.
    ./build-installer.py $BUILD_ENV 1.8.0

    # Do all of the steps above at once.
    ./release.py $BUILD_ENV_TARBALL $BUILD_ENV

