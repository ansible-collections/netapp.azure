# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: azure_rm_netapp_account'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from ansible_collections.netapp.azure.tests.unit.compat import unittest
from ansible_collections.netapp.azure.tests.unit.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from requests import Response

from ansible_collections.netapp.azure.plugins.modules.azure_rm_netapp_account \
    import AzureRMNetAppAccount as account_module

HAS_AZURE_CLOUD_ERROR_IMPORT = True
try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    HAS_AZURE_CLOUD_ERROR_IMPORT = False

if not HAS_AZURE_CLOUD_ERROR_IMPORT:
    pytestmark = pytest.mark.skip('skipping as missing required azure_exceptions')


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class MockAzureClient(object):
    ''' mock server connection to ONTAP host '''
    def __init__(self):
        ''' save arguments '''
        self.valid_accounts = ['test1', 'test2']

    def get(self, resource_group, account_name):  # pylint: disable=unused-argument
        if account_name not in self.valid_accounts:
            invalid = Response()
            invalid.status_code = 404
            raise CloudError(response=invalid)
        else:
            return Mock(name=account_name)

    def create_or_update(self, body, resource_group, account_name):  # pylint: disable=unused-argument
        return None


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.netapp_client = Mock()
        self.netapp_client.accounts = MockAzureClient()
        self._netapp_client = None

    def set_default_args(self):
        resource_group = 'azure'
        name = 'test1'
        location = 'abc'
        return dict({
            'resource_group': resource_group,
            'name': name,
            'location': location
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            account_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.__init__')
    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.netapp_client')
    def test_ensure_get_called_valid_account(self, client_f, mock_base):
        set_module_args(self.set_default_args())
        mock_base.return_value = Mock()
        client_f.return_value = Mock()
        client_f.side_effect = Mock()
        my_obj = account_module()
        # my_obj.netapp_client = self.netapp_client
        my_obj.netapp_client.accounts = self.netapp_client.accounts
        assert my_obj.get_azure_netapp_account() is not None

    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.__init__')
    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.netapp_client')
    def test_ensure_get_called_non_existing_account(self, client_f, mock_base):
        data = self.set_default_args()
        data['name'] = 'invalid'
        set_module_args(data)
        mock_base.return_value = Mock()
        client_f.return_value = Mock()
        client_f.side_effect = Mock()
        my_obj = account_module()
        my_obj.netapp_client.accounts = self.netapp_client.accounts
        assert my_obj.get_azure_netapp_account() is None

    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.__init__')
    @patch('ansible_collections.netapp.azure.plugins.modules.azure_rm_netapp_account.AzureRMNetAppAccount.get_azure_netapp_account')
    @patch('ansible_collections.netapp.azure.plugins.modules.azure_rm_netapp_account.AzureRMNetAppAccount.create_azure_netapp_account')
    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.netapp_client')
    def test_ensure_create_called(self, client_f, mock_create, mock_get, mock_base):
        data = self.set_default_args()
        data['name'] = 'create'
        data['tags'] = {'ttt': 'tesssttt', 'abc': 'xyz'}
        set_module_args(data)
        mock_get.return_value = None
        mock_base.return_value = Mock()
        client_f.return_value = Mock()
        client_f.side_effect = Mock()
        my_obj = account_module()
        my_obj.netapp_client.accounts = self.netapp_client.accounts
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.exec_module()
        assert exc.value.args[0]['changed']
        mock_create.assert_called_with()

    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.__init__')
    @patch('ansible_collections.netapp.azure.plugins.modules.azure_rm_netapp_account.AzureRMNetAppAccount.get_azure_netapp_account')
    @patch('ansible_collections.netapp.azure.plugins.modules.azure_rm_netapp_account.AzureRMNetAppAccount.delete_azure_netapp_account')
    @patch('ansible_collections.netapp.azure.plugins.module_utils.azure_rm_netapp_common.AzureRMNetAppModuleBase.netapp_client')
    def test_ensure_delete_called(self, client_f, mock_delete, mock_get, mock_base):
        data = self.set_default_args()
        data['state'] = 'absent'
        set_module_args(data)
        mock_base.return_value = Mock()
        mock_get.return_value = Mock()
        client_f.return_value = Mock()
        client_f.side_effect = Mock()
        my_obj = account_module()
        my_obj.netapp_client.accounts = self.netapp_client.accounts
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.exec_module()
        assert exc.value.args[0]['changed']
        mock_delete.assert_called_with()
