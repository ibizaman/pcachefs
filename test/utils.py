""" Utility module for tests

provides:
* WithWrapper encapsulate mock instances when used in with context
"""


class WithWrapper:
    """ Make a mock usable in a with context """
    def __init__(self, instance):
        self.instance = instance

    def __enter__(self):
        return self.instance

    def __exit__(self, *args):
        return True

