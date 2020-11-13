#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
import json
import thiscovery_lib.utilities as utils
from thiscovery_lib.core_api_utilities import CoreApiClient
from thiscovery_lib.dynamodb_utilities import Dynamodb

from common.constants import STACK_NAME, CONSENT_DATA_TABLE


class Consent:
    """
    Represents a consent item in Dynamodb
    """
    def __init__(self, core_api_client=None, correlation_id=None):
        self.project_task_id = None
        self.consent_datetime = None
        self.anon_project_specific_user_id = None
        self.anon_user_task_id = None
        self.consent_statements = None
        self.modified = None  # flag used in ddb_load method to check if ddb data was already fetched
        self._correlation_id = correlation_id
        self._ddb_client = Dynamodb(stack_name=STACK_NAME)
        self._core_api_client = core_api_client
        if core_api_client is None:
            self._core_api_client = CoreApiClient(correlation_id=correlation_id)

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if (k[0] != "_") and (k not in ['created', 'modified'])}

    def from_dict(self, consent_dict):
        self.__dict__.update(consent_dict)

    def ddb_dump(self, update_allowed=False):
        self._get_project_task_id()
        return self._ddb_client.put_item(
            table_name=CONSENT_DATA_TABLE,
            key=self.project_task_id,
            item_type='consent-data',
            item_details=self.consent_statements,
            item=self.as_dict(),
            update_allowed=update_allowed
        )

    def ddb_load(self):
        if self.modified is None:
            item = self._ddb_client.get_item(
                table_name=CONSENT_DATA_TABLE,
                key=self.project_task_id,
                key_name='project_task_id',
                sort_key={
                    'anon_project_specific_user_id': self.anon_project_specific_user_id
                },
                correlation_id=self._correlation_id
            )
            try:
                self.__dict__.update(item)
            except TypeError:
                raise utils.ObjectDoesNotExistError(
                    f'Consent item {self.project_task_id}, {self.consent_datetime} could not be found in Dynamodb',
                    details={
                        'consent_dict': self.as_dict(),
                        'correlation_id': self._correlation_id,
                    }
                )

    def _get_project_task_id(self):
        if self.project_task_id is None:
            self.project_task_id = self._core_api_client.get_user_task_from_anon_user_task_id(
                anon_user_task_id=self.anon_user_task_id
            )['project_task_id']


class ConsentEvent:
    def __init__(self, survey_consent_event):
        self.logger = survey_consent_event['logger']
        self.correlation_id = survey_consent_event['correlation_id']
        consent_dict = json.loads(survey_consent_event['body'])
        consent_embedded_data_fieldname = 'consent_statements'
        consent_dict[consent_embedded_data_fieldname] = json.loads(consent_dict[consent_embedded_data_fieldname])
        self.core_api_client = CoreApiClient(correlation_id=self.correlation_id)
        self.consent = Consent(core_api_client=self.core_api_client, correlation_id=self.correlation_id)
        self.consent.from_dict(consent_dict=consent_dict)

    def _notify_participant(self):
        counter = 1
        email_dict = dict()
        for k, v in self.consent.consent_statements.items():
            email_dict[f'consent_row_{counter:02}'] = k
            email_dict[f'consent_value_{counter:02}'] = v
            counter += 1
        self.logger.info('API call', extra={
            'email_dict': email_dict,
            'correlation_id': self.correlation_id,
        })

        return self.core_api_client.send_transactional_email(**email_dict)

    def parse(self):
        self.consent.ddb_dump()
        self._notify_participant()
