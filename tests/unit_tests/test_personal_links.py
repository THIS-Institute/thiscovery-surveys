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
import local.dev_config  # sets env variables TEST_ON_AWS and AWS_TEST_API
import local.secrets  # sets env variables THISCOVERY_AFS25_PROFILE and THISCOVERY_AMP205_PROFILE
import copy
import json
import thiscovery_dev_tools.testing_tools as test_utils
import thiscovery_lib.utilities as utils
from http import HTTPStatus
from pprint import pprint
from thiscovery_lib.dynamodb_utilities import Dynamodb

import src.personal_links as pl
import src.common.constants as const
import tests.test_data as td
from tests.testing_utilities import DdbMixin


class TestPersonalLinks(test_utils.BaseTestCase, DdbMixin):
    entity_base_url = 'v1/personal-link'

    def test_get_personal_link_api_ok(self):
        params = {
            'survey_id': td.QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id'],
            'user_id': '8518c7ed-1df4-45e9-8dc4-d49b57ae0663',  # Clive
            'account': 'cambridge',
        }
        expected_status = HTTPStatus.OK

        result = test_utils.test_get(pl.get_personal_link_api, self.entity_base_url, querystring_parameters=params)
        pprint(result)
        result_status = result['statusCode']
        result_body = json.loads(result['body'])
        self.assertEqual(expected_status, result_status)
