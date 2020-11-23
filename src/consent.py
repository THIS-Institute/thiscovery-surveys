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
import traceback
import uuid
import thiscovery_lib.utilities as utils
from dateutil import parser
from http import HTTPStatus
from thiscovery_lib.core_api_utilities import CoreApiClient
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.qualtrics import qualtrics2thiscovery_timestamp

from common.constants import STACK_NAME, CONSENT_DATA_TABLE, DEFAULT_CONSENT_EMAIL_TEMPLATE, CONSENT_ROWS_IN_TEMPLATE


class Consent:
    """
    Represents a consent item in Dynamodb
    """
    def __init__(self, consent_id=None, core_api_client=None, correlation_id=None):
        self.project_id = None
        self.project_short_name = None
        self.project_task_id = None
        self.consent_id = consent_id
        if consent_id is None:
            self.consent_id = str(uuid.uuid4())
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
        return {k: v for k, v in self.__dict__.items() if (k[0] != "_") and
                (k not in ['created', 'modified', 'details', 'type'])}

    def from_dict(self, consent_dict):
        self.__dict__.update(consent_dict)

    def ddb_dump(self, update_allowed=False):
        self._get_project()
        result = self._ddb_client.put_item(
            table_name=CONSENT_DATA_TABLE,
            key=self.project_task_id,
            key_name='project_task_id',
            item_type='qualtrics-consent-data',
            item_details=dict(),
            item=self.as_dict(),
            update_allowed=update_allowed
        )['ResponseMetadata']['HTTPStatusCode']
        assert result == HTTPStatus.OK
        return result

    def ddb_load(self):
        if self.modified is None:
            self._get_project_task_id()
            item = self._ddb_client.get_item(
                table_name=CONSENT_DATA_TABLE,
                key=self.project_task_id,
                key_name='project_task_id',
                sort_key={
                    'consent_id': self.consent_id
                },
                correlation_id=self._correlation_id
            )
            try:
                self.__dict__.update(item)
            except TypeError:
                raise utils.ObjectDoesNotExistError(
                    f'Consent item {self.project_task_id}, {self.consent_id} could not be found in Dynamodb',
                    details={
                        'consent_dict': self.as_dict(),
                        'correlation_id': self._correlation_id,
                    }
                )
            else:
                return HTTPStatus.OK

    def _get_project_task_id(self):
        if self.project_task_id is None:
            self.project_task_id = self._core_api_client.get_user_task_from_anon_user_task_id(
                anon_user_task_id=self.anon_user_task_id
            )['project_task_id']
            assert self.project_task_id

    def _get_project(self):
        if self.project_id is None:
            self._get_project_task_id()
            project = self._core_api_client.get_project_from_project_task_id(
                project_task_id=self.project_task_id
            )
            self.project_id = project['id']
            self.project_short_name = project['short_name']


class ConsentEvent:
    def __init__(self, survey_consent_event):
        self.logger = survey_consent_event['logger']
        self.correlation_id = survey_consent_event['correlation_id']
        consent_dict = json.loads(survey_consent_event['body'])
        self.participant_first_name = consent_dict['first_name']
        self.consent_info_url = consent_dict['consent_info_url']
        del consent_dict['first_name']
        del consent_dict['consent_info_url']
        consent_embedded_data_fieldname = 'consent_statements'
        consent_dict[consent_embedded_data_fieldname] = json.loads(consent_dict[consent_embedded_data_fieldname])
        try:
            self.template_name = consent_dict['template_name']
        except KeyError:
            self.template_name = DEFAULT_CONSENT_EMAIL_TEMPLATE
        else:
            del consent_dict['template_name']
        try:
            consent_dict['consent_datetime'] = qualtrics2thiscovery_timestamp(consent_dict['consent_datetime'])
        except KeyError:
            consent_dict['consent_datetime'] = str(utils.now_with_tz())
        self.core_api_client = CoreApiClient(correlation_id=self.correlation_id)
        self.consent = Consent(core_api_client=self.core_api_client, correlation_id=self.correlation_id)
        self.consent.from_dict(consent_dict=consent_dict)

    def _format_consent_statements(self):
        counter = 0
        custom_properties_dict = dict()
        for statement_dict in self.consent.consent_statements:
            counter += 1
            key = list(statement_dict.keys())[0]
            custom_properties_dict[f'consent_row_{counter:02}'] = key
            custom_properties_dict[f'consent_value_{counter:02}'] = statement_dict[key]
        if counter > CONSENT_ROWS_IN_TEMPLATE:
            raise utils.DetailedValueError('Number of consent statements exceeds maximum supported by template', details={
                'len_consent_statements': len(self.consent.consent_statements),
                'consent_statements': self.consent.consent_statements,
                'rows_in_template': CONSENT_ROWS_IN_TEMPLATE,
                'correlation_id': self.correlation_id,
            })
        while counter < CONSENT_ROWS_IN_TEMPLATE:
            counter += 1
            custom_properties_dict[f'consent_row_{counter:02}'] = str()
            custom_properties_dict[f'consent_value_{counter:02}'] = str()
        return custom_properties_dict

    def _split_consent_datetime(self):
        consent_dt = parser.parse(self.consent.consent_datetime)
        date = consent_dt.strftime('%e %B %Y')
        time = consent_dt.strftime('%H:%M')
        return date, time

    def _notify_participant(self):
        custom_properties_dict = self._format_consent_statements()
        custom_properties_dict['user_first_name'] = self.participant_first_name
        custom_properties_dict['consent_info_url'] = self.consent_info_url
        custom_properties_dict['project_short_name'] = self.consent.project_short_name
        custom_properties_dict['current_date'], custom_properties_dict['current_time'] = self._split_consent_datetime()
        email_dict = dict()
        email_dict['custom_properties'] = custom_properties_dict
        self.logger.info('API call', extra={
            'email_dict': email_dict,
            'correlation_id': self.correlation_id,
        })
        template_name = self.template_name
        email_dict['to_recipient_id'] = self.consent.anon_project_specific_user_id
        return self.core_api_client.send_transactional_email(
            template_name=template_name, **email_dict
        )

    def parse(self):
        dump_result = None
        try:
            dump_result = self.consent.ddb_dump()
        except:
            self.logger.error('Failed to store consent data in Dynamodb', extra={
                'consent_as_dict': self.consent.as_dict(),
                'correlation_id': self.correlation_id,
                'traceback': traceback.format_exc(),
            })
        notification_result = self._notify_participant().get('statusCode')
        assert notification_result == HTTPStatus.NO_CONTENT
        return dump_result, notification_result
