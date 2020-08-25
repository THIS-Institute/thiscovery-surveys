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
from http import HTTPStatus

import src.endpoints as ep
import tests.testing_utilities as test_utils
from tests.test_data import QUALTRICS_TEST_OBJECTS
from src.common.utilities import set_running_unit_tests


class BaseSurveyTestCase(unittest.TestCase):
    maxDiff = None
    test_survey_id = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id']
    test_response_id = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['response_2_id']
    test_question_ids = [
        'Q12_1',
        'Q12_2',
        'Q12_3',
        'Q12_4',
        'Q12_5',
        'Q12_6',
        'Q12_7',
        'Q12_8',
        'Q1',
        'Q1COM',
        'Q12_8_TEXT',
        'Q4',
        'Q4COM'
    ]

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)


class TestSurveyClient(BaseSurveyTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.survey_client = ep.SurveyClient(cls.test_survey_id)

    def test_sc_01_get_response_ok(self):
        response = self.survey_client.get_response(self.test_response_id)
        self.assertCountEqual(QUALTRICS_TEST_OBJECTS['unittest-survey-1']['export_tags'], list(response.keys()))

    def test_sc_01_get_response_ok_omit_null_values(self):
        response = self.survey_client.get_response(self.test_response_id, return_nulls=False)
        questions_with_null_answers = [
            'Q1COM_DO',
            'Q4COM_DO',
            'RecipientEmail',
            'Q3COM',
            'Q2COM_DO',
            'RecipientLastName',
            'RecipientFirstName',
            'ExternalReference',
            'Q4',
            'Q4COM',
            'Q3COM_DO',
        ]
        expected_keys = [x for x in QUALTRICS_TEST_OBJECTS['unittest-survey-1']['export_tags'] if x not in questions_with_null_answers]
        self.assertCountEqual(expected_keys, list(response.keys()))


class TestEndpoints(BaseSurveyTestCase):

    def test_ep_01_get_response_api_ok(self):
        body_dict = {
            'survey_id': self.test_survey_id,
            'response_id': self.test_response_id,
            'question_ids': self.test_question_ids
        }
        body = json.dumps(body_dict)
        result = test_utils.test_post(
            local_method=ep.get_responses_api,
            aws_url=None,
            request_body=body,
        )
        self.assertEqual(HTTPStatus.OK, result['statusCode'])
        expected_result_body = {
            "Q12_1": 1,
            "Q12_2": 1,
            "Q12_3": 1,
            "Q12_4": 1,
            "Q12_5": 1,
            "Q12_6": 1,
            "Q12_7": 1,
            "Q12_8": 1,
            "Q1": 1,
            "Q1COM": "Good job.",
            "Q12_8_TEXT": "Smoke signals",
            "Q4": None,
            "Q4COM": None,
        }
        self.assertCountEqual(expected_result_body, json.loads(result['body']))

    def test_ep_03_get_response_api_ok_question_ids_not_specified(self):
        body_dict = {
            'survey_id': self.test_survey_id,
            'response_id': self.test_response_id,
        }
        body = json.dumps(body_dict)
        result = test_utils.test_post(
            local_method=ep.get_responses_api,
            aws_url=None,
            request_body=body,
        )
        self.assertEqual(HTTPStatus.OK, result['statusCode'])
        expected_result_body_keys = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['export_tags']

        self.assertCountEqual(expected_result_body_keys, json.loads(result['body']).keys())
