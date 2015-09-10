# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import mock
from oslo_policy import policy

from magnum.api.controllers.v1 import certificate as api_cert
from magnum.common import utils
from magnum.tests import base
from magnum.tests.unit.api import base as api_base
from magnum.tests.unit.api import utils as apiutils
from magnum.tests.unit.objects import utils as obj_utils


class TestCertObject(base.TestCase):

    @mock.patch('magnum.api.controllers.v1.utils.get_rpc_resource')
    def test_cert_init(self, mock_get_rpc_resource):
        cert_dict = apiutils.cert_post_data()
        mock_bay = mock.MagicMock()
        mock_bay.uuid = cert_dict['bay_uuid']
        mock_get_rpc_resource.return_value = mock_bay

        cert = api_cert.Certificate(**cert_dict)

        self.assertEqual(cert.bay_uuid, cert_dict['bay_uuid'])
        self.assertEqual(cert.csr, cert_dict['csr'])
        self.assertEqual(cert.pem, cert_dict['pem'])


class TestGetCertificate(api_base.FunctionalTest):

    def setUp(self):
        super(TestGetCertificate, self).setUp()
        self.bay = obj_utils.create_test_bay(self.context)

        conductor_api_patcher = mock.patch('magnum.conductor.api.API')
        self.conductor_api_class = conductor_api_patcher.start()
        self.conductor_api = mock.MagicMock()
        self.conductor_api_class.return_value = self.conductor_api
        self.addCleanup(conductor_api_patcher.stop)

    def test_get_one(self):
        fake_cert = apiutils.cert_post_data()
        mock_cert = mock.MagicMock()
        mock_cert.as_dict.return_value = fake_cert
        self.conductor_api.get_ca_certificate.return_value = mock_cert

        response = self.get_json('/certificates/%s' % self.bay.uuid)

        self.assertEqual(response['bay_uuid'], self.bay.uuid)
        self.assertEqual(response['csr'], fake_cert['csr'])
        self.assertEqual(response['pem'], fake_cert['pem'])

    def test_get_one_by_name(self):
        fake_cert = apiutils.cert_post_data()
        mock_cert = mock.MagicMock()
        mock_cert.as_dict.return_value = fake_cert
        self.conductor_api.get_ca_certificate.return_value = mock_cert

        response = self.get_json('/certificates/%s' % self.bay.name)

        self.assertEqual(response['bay_uuid'], self.bay.uuid)
        self.assertEqual(response['csr'], fake_cert['csr'])
        self.assertEqual(response['pem'], fake_cert['pem'])

    def test_get_one_by_name_not_found(self):
        response = self.get_json('/certificates/not_found',
                                 expect_errors=True)

        self.assertEqual(404, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])

    def test_get_one_by_name_multiple_bay(self):
        obj_utils.create_test_bay(self.context, name='test_bay',
                                  uuid=utils.generate_uuid())
        obj_utils.create_test_bay(self.context, name='test_bay',
                                  uuid=utils.generate_uuid())

        response = self.get_json('/certificates/test_bay',
                                 expect_errors=True)

        self.assertEqual(409, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])

    def test_links(self):
        fake_cert = apiutils.cert_post_data()
        mock_cert = mock.MagicMock()
        mock_cert.as_dict.return_value = fake_cert
        self.conductor_api.get_ca_certificate.return_value = mock_cert

        response = self.get_json('/certificates/%s' % self.bay.uuid)

        self.assertIn('links', response.keys())
        self.assertEqual(2, len(response['links']))
        self.assertIn(self.bay.uuid, response['links'][0]['href'])
        for l in response['links']:
            bookmark = l['rel'] == 'bookmark'
            self.assertTrue(self.validate_link(l['href'], bookmark=bookmark))


class TestPost(api_base.FunctionalTest):

    def setUp(self):
        super(TestPost, self).setUp()
        self.bay = obj_utils.create_test_bay(self.context)

        conductor_api_patcher = mock.patch('magnum.conductor.api.API')
        self.conductor_api_class = conductor_api_patcher.start()
        self.conductor_api = mock.MagicMock()
        self.conductor_api_class.return_value = self.conductor_api
        self.addCleanup(conductor_api_patcher.stop)

        self.conductor_api.sign_certificate.side_effect = self._fake_sign

    @staticmethod
    def _fake_sign(bay, cert):
        cert.pem = 'fake-pem'
        return cert

    def test_create_cert(self, ):
        new_cert = apiutils.cert_post_data(bay_uuid=self.bay.uuid)
        del new_cert['pem']

        response = self.post_json('/certificates', new_cert)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(201, response.status_int)
        self.assertEqual(response.json['bay_uuid'], new_cert['bay_uuid'])
        self.assertEqual(response.json['pem'], 'fake-pem')

    def test_create_cert_by_bay_name(self, ):
        new_cert = apiutils.cert_post_data(bay_uuid=self.bay.name)
        del new_cert['pem']

        response = self.post_json('/certificates', new_cert)

        self.assertEqual('application/json', response.content_type)
        self.assertEqual(201, response.status_int)
        self.assertEqual(response.json['bay_uuid'], self.bay.uuid)
        self.assertEqual(response.json['pem'], 'fake-pem')

    def test_create_cert_bay_not_found(self, ):
        new_cert = apiutils.cert_post_data(bay_uuid='not_found')
        del new_cert['pem']

        response = self.post_json('/certificates', new_cert,
                                  expect_errors=True)

        self.assertEqual(400, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])


class TestCertPolicyEnforcement(api_base.FunctionalTest):

    def setUp(self):
        super(TestCertPolicyEnforcement, self).setUp()

    def _common_policy_check(self, rule, func, *arg, **kwarg):
        self.policy.set_rules({rule: "project:non_fake"})
        exc = self.assertRaises(policy.PolicyNotAuthorized,
                                func, *arg, **kwarg)
        self.assertTrue(exc.message.startswith(rule))
        self.assertTrue(exc.message.endswith("disallowed by policy"))

    def test_policy_disallow_get_one(self):
        self._common_policy_check(
            "certificate:get", self.get_json,
            '/certificates/ce5da569-4f65-4272-9199-fac8c9fbc9d4')

    def test_policy_disallow_create(self):
        cert = apiutils.cert_post_data()
        self._common_policy_check(
            "certificate:create", self.post_json, '/certificates', cert)
