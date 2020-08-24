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
import unittest
from pprint import pprint

import src.endpoints as ep
import src.common.qualtrics as qualtrics
import tests.testing_utilities as test_utils
from local.dev_config import QUALTRICS_TEST_OBJECTS
from src.common.utilities import set_running_unit_tests


class TestEndpoints(unittest.TestCase):
    test_survey_id = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id']
    test_response_id = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['response_1_id']

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_01_get_response_api_ok(self):
        body_dict = {
            'survey_id': self.test_survey_id,
            'response_id': self.test_response_id,
            'question_ids': [
                'QID1',
                'QID3',
                'QID5',
                'QID7',
            ]
        }
        body = json.dumps(body_dict)
        result = test_utils.test_post(
            local_method=ep.get_responses_api,
            aws_url=None,
            request_body=body,
        )
        pprint(result)
