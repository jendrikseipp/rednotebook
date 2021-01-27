def pytest_configure(config):
    import builtins

    if not hasattr(builtins, "_"):
        builtins._ = lambda x: x
