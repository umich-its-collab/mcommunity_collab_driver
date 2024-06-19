import pytest
from requests import HTTPError
from mcommunity_collab_driver import mcommunity


def test_MCommClient():
    with pytest.raises(HTTPError):
        mcommunity.MCommClient('dfasf', 'adsrasdr', 'fadsr', 'rick-test','https://mcommunity.umich.edu/api' )