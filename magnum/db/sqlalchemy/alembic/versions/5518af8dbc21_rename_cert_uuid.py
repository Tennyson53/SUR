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
"""Rename cert_uuid

Revision ID: 5518af8dbc21
Revises: 6f21dc920bb
Create Date: 2015-08-28 13:13:19.747625

"""

# revision identifiers, used by Alembic.
revision = '5518af8dbc21'
down_revision = '6f21dc920bb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('bay', 'ca_cert_uuid',
                    new_column_name='ca_cert_ref',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=512),
                    nullable=True)
    op.alter_column('bay', 'magnum_cert_uuid',
                    new_column_name='magnum_cert_ref',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=512),
                    nullable=True)
