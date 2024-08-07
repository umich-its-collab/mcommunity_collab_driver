import requests


class MCommError(Exception):

    # Constructor or Initializer
    def __init__(self, value):
        self.value = value

    # __str__ is to print() the value
    def __str__(self):
        return f'{self.value.status_code} {self.value.text}'


class MCommClient:
    def __init__(self, username: object, password: object, app_id: object, full_name: object, uri: object):
        """

        :param username:
        :param password:
        :param app_id:
        :param full_name:
        :param uri:

        """

        self.username = username
        self.password = password
        self.uri = uri
        self.app_id = app_id
        self.full_name = full_name
        self.auth = self._get_auth_token()

    def _get_auth_token(self) -> dict:

        """

        Returns Authorization Token for use when accessing MCommunity Resources.

        :rtype: Json

        """
        token_uri = f'{self.uri}/token/'
        token_body = {'username': self.username, 'password': self.password}
        response = requests.post(token_uri, data=token_body)
        response.raise_for_status()
        access_token = response.json().get('access')
        return {'Authorization': f'Bearer {access_token}'}

    def group(self, group: object) -> object:
        """

        :rtype: object
        :param group:
        :return:
        """
        return self.Group(self, group)

    class Group:
        def __init__(self, mcommclient: object, mcomm_group: object = ''):
            """

            :param mcommclient:
            :param mcomm_group:
            :rtype: object
            """
            self.exists = False
            self.group_name = mcomm_group
            self.mcommclient = mcommclient
            self.group_uri = f'{mcommclient.uri}/groups/{self.group_name}/'
            self._get_group_info()

        def _get_group_info(self):
            """
            Gets info for group.
            """
            response = requests.get(self.group_uri, headers=self.mcommclient.auth)
            if response.status_code == 200:
                self.exists = True
                group_data = response.json()
                self.owners = [owner.split(',')[0].split('=')[1] for owner in group_data['owner']]
                self.members = [member.split(',')[0].split('=')[1] for member in group_data.get('member', '') if
                                'uid=' in member]
                self.externalMembers = group_data.get('rfc822mail', [])
                self.aliases = group_data.get('cn', '')
                self.memberGroups = [group.split(',')[0].split('=')[1] for group in group_data.get('groupMember', '') if
                                     'cn=' in group]

        def _update_attribute(self, attribute_name: object, data: object):
            """
            Takes in an attribute_name and data payload for update.

            :param attribute_name:
            :param data:
            """
            response = requests.post(f'{self.group_uri}{attribute_name}/', headers=self.mcommclient.auth, data=data)
            if response.status_code != 200:
                raise (MCommError(response))

        def update_aliases(self):
            """
            adds an alias to an MCommunity group if the alias does not exist.
            """
            group_data = requests.get(self.group_uri, headers=self.mcommclient.auth).json()
            og_aliases = group_data.get('cn', '')
            for alias in self.aliases:
                if alias not in og_aliases:
                    self._update_attribute('cn', {'add': [alias]})

        def update_ownership(self):
            """
            Checks if new owner is a group or user and than adds it to MCommunity
            """
            group_data = requests.get(self.group_uri, headers=self.mcommclient.auth).json()
            og_owners = [owner.split(',')[0].split('=')[1] for owner in group_data['owner']]
            for owner in self.owners:
                if owner not in og_owners and len(owner) > 8:
                    self._update_attribute('owner', {'add': f'cn={owner},ou=User Groups,ou=Groups,dc=umich,dc=edu'})
                elif owner not in og_owners and len(owner) > 0:
                    self._update_attribute('owner', {'add': f'uid={owner},ou=People,dc=umich,dc=edu'})

        def update_membership(self):
            """
            Checks if new members are already exist and if they do not than the member is added based on it's type
            """
            group_data = requests.get(self.group_uri, headers=self.mcommclient.auth).json()
            og_external = group_data.get('rfc822mail', [])
            og_member_groups = [group.split(',')[0].split('=')[1] for group in group_data.get('groupMember', '') if
                                'cn=' in group]
            og_members = [member.split(',')[0].split('=')[1] for member in group_data.get('member', '') if
                          'uid=' in member]
            for member in self.members:
                if member not in og_members:
                    self._update_attribute('member', {'add': f'uid={member},ou=People,dc=umich,dc=edu'})
            for member in self.externalMembers:
                if member not in og_external:
                    self._update_attribute('rfc822mail', {'add': member})
            for member in self.memberGroups:
                if member not in og_member_groups:
                    self._update_attribute('groupMember',
                                           {'add': f'cn={member},ou=User Groups,ou=Groups,dc=umich,dc=edu'})

        def reserve(self):
            """
            Reserve's a Group before adding parameters
            """
            group_data = {
                'cn': f'{self.mcommclient.full_name}',
                'umichGroupEmail': f'{self.group_name}',
                'owner': [f'cn={self.mcommclient.app_id},ou=User Groups,ou=Groups,dc=umich,dc=edu'],
                'umichDescription': ''
            }
            response = requests.post(f'{self.mcommclient.uri}/groups/', headers=self.mcommclient.auth, data=group_data)
            if response.status_code != 201:
                raise (MCommError(response))
            self._get_group_info()


