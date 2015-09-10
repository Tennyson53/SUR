# Copyright 2014, 2015 Rackspace US, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid

from barbicanclient import client as barbican_client
from barbicanclient import containers
from barbicanclient import secrets
import mock
from mock import patch

from magnum.common.cert_manager import barbican_cert_manager as bcm
from magnum.common.cert_manager import cert_manager
from magnum.tests import base


class TestBarbicanCert(base.BaseTestCase):

    def setUp(self):
        # Certificate data
        self.certificate = "My Certificate"
        self.intermediates = "My Intermediates"
        self.private_key = "My Private Key"
        self.private_key_passphrase = "My Private Key Passphrase"

        self.certificate_secret = barbican_client.secrets.Secret(
            api=mock.MagicMock(),
            payload=self.certificate
        )
        self.intermediates_secret = barbican_client.secrets.Secret(
            api=mock.MagicMock(),
            payload=self.intermediates
        )
        self.private_key_secret = barbican_client.secrets.Secret(
            api=mock.MagicMock(),
            payload=self.private_key
        )
        self.private_key_passphrase_secret = barbican_client.secrets.Secret(
            api=mock.MagicMock(),
            payload=self.private_key_passphrase
        )

        super(TestBarbicanCert, self).setUp()

    def test_barbican_cert(self):
        container = barbican_client.containers.CertificateContainer(
            api=mock.MagicMock(),
            certificate=self.certificate_secret,
            intermediates=self.intermediates_secret,
            private_key=self.private_key_secret,
            private_key_passphrase=self.private_key_passphrase_secret
        )
        # Create a cert
        cert = bcm.Cert(
            cert_container=container
        )

        # Validate the cert functions
        self.assertEqual(cert.get_certificate(), self.certificate)
        self.assertEqual(cert.get_intermediates(), self.intermediates)
        self.assertEqual(cert.get_private_key(), self.private_key)
        self.assertEqual(cert.get_private_key_passphrase(),
                         self.private_key_passphrase)

    def test_barbican_cert_none_values(self):
        container = barbican_client.containers.CertificateContainer(
            api=mock.MagicMock(),
            certificate=None,
            intermediates=None,
            private_key=None,
            private_key_passphrase=None
        )
        # Create a cert
        cert = bcm.Cert(
            cert_container=container
        )

        # Validate the cert functions
        self.assertEqual(cert.get_certificate(), None)
        self.assertEqual(cert.get_intermediates(), None)
        self.assertEqual(cert.get_private_key(), None)
        self.assertEqual(cert.get_private_key_passphrase(), None)


class TestBarbicanManager(base.BaseTestCase):

    def setUp(self):
        # Make a fake Container and contents
        self.barbican_endpoint = 'http://localhost:9311/v1'
        self.container_uuid = uuid.uuid4()

        self.container_ref = '{0}/containers/{1}'.format(
            self.barbican_endpoint, self.container_uuid
        )

        self.name = 'My Fancy Cert'
        self.private_key = mock.Mock(spec=secrets.Secret)
        self.certificate = mock.Mock(spec=secrets.Secret)
        self.intermediates = mock.Mock(spec=secrets.Secret)
        self.private_key_passphrase = mock.Mock(spec=secrets.Secret)

        container = mock.Mock(spec=containers.CertificateContainer)
        container.container_ref = self.container_ref
        container.name = self.name
        container.private_key = self.private_key
        container.certificate = self.certificate
        container.intermediates = self.intermediates
        container.private_key_passphrase = self.private_key_passphrase
        self.container = container

        self.empty_container = mock.Mock(spec=containers.CertificateContainer)

        self.secret1 = mock.Mock(spec=secrets.Secret)
        self.secret2 = mock.Mock(spec=secrets.Secret)
        self.secret3 = mock.Mock(spec=secrets.Secret)
        self.secret4 = mock.Mock(spec=secrets.Secret)

        super(TestBarbicanManager, self).setUp()

    @patch('magnum.common.clients.OpenStackClients.barbican')
    def test_store_cert(self, mock_barbican):
        # Mock out the client
        bc = mock.MagicMock()
        bc.containers.create_certificate.return_value = self.empty_container
        mock_barbican.return_value = bc

        # Attempt to store a cert
        bcm.CertManager.store_cert(
            certificate=self.certificate,
            private_key=self.private_key,
            intermediates=self.intermediates,
            private_key_passphrase=self.private_key_passphrase,
            name=self.name
        )

        # create_secret should be called four times with our data
        calls = [
            mock.call(payload=self.certificate, expiration=None,
                      name=mock.ANY),
            mock.call(payload=self.private_key, expiration=None,
                      name=mock.ANY),
            mock.call(payload=self.intermediates, expiration=None,
                      name=mock.ANY),
            mock.call(payload=self.private_key_passphrase, expiration=None,
                      name=mock.ANY)
        ]
        bc.secrets.create.assert_has_calls(calls, any_order=True)

        # create_certificate should be called once
        self.assertEqual(bc.containers.create_certificate.call_count, 1)

        # Container should be stored once
        self.empty_container.store.assert_called_once_with()

    @patch('magnum.common.clients.OpenStackClients.barbican')
    def test_store_cert_failure(self, mock_barbican):
        # Mock out the client
        bc = mock.MagicMock()
        bc.containers.create_certificate.return_value = self.empty_container
        test_secrets = [
            self.secret1,
            self.secret2,
            self.secret3,
            self.secret4
        ]
        bc.secrets.create.side_effect = test_secrets
        self.empty_container.store.side_effect = ValueError()
        mock_barbican.return_value = bc

        # Attempt to store a cert
        self.assertRaises(
            ValueError,
            bcm.CertManager.store_cert,
            certificate=self.certificate,
            private_key=self.private_key,
            intermediates=self.intermediates,
            private_key_passphrase=self.private_key_passphrase,
            name=self.name
        )

        # create_secret should be called four times with our data
        calls = [
            mock.call(payload=self.certificate, expiration=None,
                      name=mock.ANY),
            mock.call(payload=self.private_key, expiration=None,
                      name=mock.ANY),
            mock.call(payload=self.intermediates, expiration=None,
                      name=mock.ANY),
            mock.call(payload=self.private_key_passphrase, expiration=None,
                      name=mock.ANY)
        ]
        bc.secrets.create.assert_has_calls(calls, any_order=True)

        # create_certificate should be called once
        self.assertEqual(bc.containers.create_certificate.call_count, 1)

        # Container should be stored once
        self.empty_container.store.assert_called_once_with()

        # All secrets should be deleted (or at least an attempt made)
        for s in test_secrets:
            s.delete.assert_called_once_with()

    @patch('magnum.common.clients.OpenStackClients.barbican')
    def test_get_cert(self, mock_barbican):
        # Mock out the client
        bc = mock.MagicMock()
        bc.containers.register_consumer.return_value = self.container
        mock_barbican.return_value = bc

        # Get the container data
        data = bcm.CertManager.get_cert(
            cert_ref=self.container_ref,
            resource_ref=self.container_ref,
            service_name='Magnum'
        )

        # 'register_consumer' should be called once with the container_ref
        bc.containers.register_consumer.assert_called_once_with(
            container_ref=self.container_ref,
            url=self.container_ref,
            name='Magnum'
        )

        # The returned data should be a Cert object with the correct values
        self.assertIsInstance(data, cert_manager.Cert)
        self.assertEqual(data.get_private_key(),
                         self.private_key.payload)
        self.assertEqual(data.get_certificate(),
                         self.certificate.payload)
        self.assertEqual(data.get_intermediates(),
                         self.intermediates.payload)
        self.assertEqual(data.get_private_key_passphrase(),
                         self.private_key_passphrase.payload)

    @patch('magnum.common.clients.OpenStackClients.barbican')
    def test_get_cert_no_registration(self, mock_barbican):
        # Mock out the client
        bc = mock.MagicMock()
        bc.containers.get.return_value = self.container
        mock_barbican.return_value = bc

        # Get the container data
        data = bcm.CertManager.get_cert(
            cert_ref=self.container_ref, check_only=True
        )

        # 'get' should be called once with the container_ref
        bc.containers.get.assert_called_once_with(
            container_ref=self.container_ref
        )

        # The returned data should be a Cert object with the correct values
        self.assertIsInstance(data, cert_manager.Cert)
        self.assertEqual(data.get_private_key(),
                         self.private_key.payload)
        self.assertEqual(data.get_certificate(),
                         self.certificate.payload)
        self.assertEqual(data.get_intermediates(),
                         self.intermediates.payload)
        self.assertEqual(data.get_private_key_passphrase(),
                         self.private_key_passphrase.payload)

    @patch('magnum.common.clients.OpenStackClients.barbican')
    def test_delete_cert(self, mock_barbican):
        # Mock out the client
        bc = mock.MagicMock()
        mock_barbican.return_value = bc

        # Attempt to deregister as a consumer
        bcm.CertManager.delete_cert(
            cert_ref=self.container_ref,
            resource_ref=self.container_ref,
            service_name='Magnum'
        )

        # remove_consumer should be called once with the container_ref
        bc.containers.remove_consumer.assert_called_once_with(
            container_ref=self.container_ref,
            url=self.container_ref,
            name='Magnum'
        )

    @patch('magnum.common.clients.OpenStackClients.barbican')
    def test_actually_delete_cert(self, mock_barbican):
        # Mock out the client
        bc = mock.MagicMock()
        bc.containers.get.return_value = self.container
        mock_barbican.return_value = bc

        # Attempt to store a cert
        bcm.CertManager._actually_delete_cert(
            cert_ref=self.container_ref
        )

        # All secrets should be deleted
        self.container.certificate.delete.assert_called_once_with()
        self.container.private_key.delete.assert_called_once_with()
        self.container.intermediates.delete.assert_called_once_with()
        self.container.private_key_passphrase.delete.assert_called_once_with()

        # Container should be deleted once
        self.container.delete.assert_called_once_with()
