from unittest.mock import patch, Mock, call

import pytest, requests

from mcommunity_collab_driver.mcommunity import MCommClient, MCommError


@pytest.fixture
def mcomm_client():
    with patch('mcommunity_collab_driver.mcommunity.MCommClient._get_auth_token') as mock_auth:
        mock_auth.return_value = {'Authorization': 'Bearer test_token'}
        return MCommClient("testuser", "test_pass", "test_app_id", "Test FullName", "http://testuri.com")


@pytest.fixture
def mcomm_client_group(mcomm_client):
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'owner': ['uid=owner1,ou=People,dc=umich,dc=edu'],
            'member': ['uid=member1,ou=People,dc=umich,dc=edu'],
            'rfc822mail': ['external@example.com'],
            'cn': ['alias1'],
            'groupMember': ['cn=group1,ou=User Groups,ou=Groups,dc=umich,dc=edu']
        }
        mock_get.return_value = mock_response

        group = mcomm_client.group('test_group')
        return group


def test_get_auth_token(mcomm_client):
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access': 'test_token'}
        mock_post.return_value = mock_response

        auth_token = mcomm_client._get_auth_token()
        assert auth_token == {'Authorization': 'Bearer test_token'}
        mock_post.assert_called_once_with(
            'http://testuri.com/token/',
            data={'username': 'testuser', 'password': 'test_pass'}
        )


def test_group_init(mcomm_client):
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'owner': ['uid=owner1,ou=People,dc=umich,dc=edu'],
            'member': ['uid=member1,ou=People,dc=umich,dc=edu'],
            'rfc822mail': ['external@example.com'],
            'cn': ['alias1'],
            'groupMember': ['cn=group1,ou=User Groups,ou=Groups,dc=umich,dc=edu']
        }
        mock_get.return_value = mock_response

        group = mcomm_client.group('test_group')
        assert group.exists
        assert group.owners == ['owner1']
        assert group.members == ['member1']
        assert group.externalMembers == ['external@example.com']
        assert group.aliases == ['alias1']
        assert group.memberGroups == ['group1']
        mock_get.assert_called_once_with('http://testuri.com/groups/test_group/',
                                         headers={'Authorization': 'Bearer test_token'})


def test_update_attribute(mcomm_client_group):
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        mcomm_client_group._update_attribute('cn', {'add': 'new_alias'})
        mock_post.assert_called_once_with(
            'http://testuri.com/groups/test_group/cn/',
            headers={'Authorization': 'Bearer test_token'},
            data={'add': 'new_alias'}
        )


def test_update_aliases(mcomm_client_group):
    with patch('mcommunity_collab_driver.mcommunity.requests.get') as mock_get, \
            patch('mcommunity_collab_driver.mcommunity.requests.post') as mock_post:
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'cn': ['alias1'],
            'owner': ['uid=owner1,ou=People,dc=umich,dc=edu']
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        group = mcomm_client_group
        group.aliases = ['alias1', 'alias2']
        group.update_aliases()

        mock_post.assert_called_once_with(
            'http://testuri.com/groups/test_group/cn/',
            headers={'Authorization': 'Bearer test_token'},
            data={'add': ['alias2']}
        )


def test_update_ownership(mcomm_client_group):
    with patch('mcommunity_collab_driver.mcommunity.requests.get') as mock_get, \
            patch('mcommunity_collab_driver.mcommunity.requests.post') as mock_post:
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'owner': ['uid=owner1,ou=People,dc=umich,dc=edu']
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        group = mcomm_client_group
        group.owners = ['owner1', 'newowner']
        group.update_ownership()

        mock_post.assert_called_once_with(
            'http://testuri.com/groups/test_group/owner/',
            headers={'Authorization': 'Bearer test_token'},
            data={'add': 'uid=newowner,ou=People,dc=umich,dc=edu'}
        )


def test_update_membership(mcomm_client_group):
    with patch('mcommunity_collab_driver.mcommunity.requests.get') as mock_get, \
            patch('mcommunity_collab_driver.mcommunity.requests.post') as mock_post:
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'member': ['uid=member1,ou=People,dc=umich,dc=edu'],
            'rfc822mail': ['external@example.com'],
            'groupMember': ['cn=group1,ou=User Groups,ou=Groups,dc=umich,dc=edu']
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        group = mcomm_client_group
        group.members = ['member1', 'member2']
        group.externalMembers = ['external@example.com', 'new_external@example.com']
        group.memberGroups = ['group1', 'group2']
        group.update_membership()

        post_calls = [
            call('http://testuri.com/groups/test_group/member/', headers={'Authorization': 'Bearer test_token'},
                 data={'add': 'uid=member2,ou=People,dc=umich,dc=edu'}),
            call('http://testuri.com/groups/test_group/rfc822mail/', headers={'Authorization': 'Bearer test_token'},
                 data={'add': 'new_external@example.com'}),
            call('http://testuri.com/groups/test_group/groupMember/', headers={'Authorization': 'Bearer test_token'},
                 data={'add': 'cn=group2,ou=User Groups,ou=Groups,dc=umich,dc=edu'})
        ]

        mock_post.assert_has_calls(post_calls, any_order=True)


def test_reserve(mcomm_client_group):
    with patch('mcommunity_collab_driver.mcommunity.requests.post') as mock_post, \
            patch('mcommunity_collab_driver.mcommunity.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'owner': ['uid=owner1,ou=People,dc=umich,dc=edu'],
            'member': ['uid=member1,ou=People,dc=umich,dc=edu'],
            'rfc822mail': ['external@example.com'],
            'cn': ['alias1'],
            'groupMember': ['cn=group1,ou=User Groups,ou=Groups,dc=umich,dc=edu']
        }
        mock_get.return_value = mock_get_response

        group = mcomm_client_group
        group.reserve()
        mock_post.assert_called_once_with(
            'http://testuri.com/groups/',
            headers={'Authorization': 'Bearer test_token'},
            data={
                'cn': 'Test FullName',
                'umichGroupEmail': 'test_group',
                'owner': ['cn=test_app_id,ou=User Groups,ou=Groups,dc=umich,dc=edu'],
                'umichDescription': ''
            }
        )


def test_reserve_failure(mcomm_client):
    with patch('mcommunity_collab_driver.mcommunity.requests.post') as mock_post, \
            patch('mcommunity_collab_driver.mcommunity.requests.get'):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        group = mcomm_client.group('new_group')
        with pytest.raises(MCommError):
            group.reserve()
