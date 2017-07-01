import pytest
from mockito import unstub

@pytest.fixture(autouse=True)
def removeMocks(request):
    """ Fixture to automatically unstub after tests

    This is needed when stubbing low-level stuff like os or os.path.
    """
    request.addfinalizer(unstub)
