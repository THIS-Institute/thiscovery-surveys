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
import local.dev_config
import local.secrets
import json
import os
from http import HTTPStatus
from thiscovery_dev_tools.testing_tools import TestApiEndpoints, TestSecurityOfEndpointsDefinedInTemplateYaml

from tests.test_data import QUALTRICS_TEST_OBJECTS, BASE_FOLDER, TEST_RESPONSE_DICT, TEST_CONSENT_EVENT


class TestSurveysApiEndpoints(TestApiEndpoints):

    def test_get_response_requires_valid_key(self):
        params = {
            'survey_id': QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id'],
            'response_id': QUALTRICS_TEST_OBJECTS['unittest-survey-1']['response_2_id'],
        }
        self.check_api_is_restricted(
            request_verb='GET',
            aws_url='v1/response',
            querystring_parameters=params,
        )

    def test_put_response_requires_valid_key(self):
        self.check_api_is_restricted(
            request_verb='PUT',
            aws_url='v1/response',
            request_body=json.dumps(TEST_RESPONSE_DICT),
        )

    def test_send_consent_email_requires_valid_key(self):
        self.check_api_is_restricted(
            request_verb='POST',
            aws_url='v1/send-consent-email',
            request_body=TEST_CONSENT_EVENT['body'],
        )


class TestTemplate(TestSecurityOfEndpointsDefinedInTemplateYaml):
    public_endpoints = [
        ('/v1/raise-error', 'post'),
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass(
            template_file_path=os.path.join(BASE_FOLDER, 'template.yaml'),
            api_resource_name='SurveysApi',
        )

    def test_defined_endpoints_are_secure(self):
        self.check_defined_endpoints_are_secure()
