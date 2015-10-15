def pytest_configure(config):
    import __builtin__
    if not hasattr(__builtin__, '_'):
        __builtin__._ = lambda x: x
