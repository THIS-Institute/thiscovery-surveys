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
import unittest
from http import HTTPStatus
from pprint import pprint

import thiscovery_lib.utilities as utils
import src.endpoints as ep
import thiscovery_dev_tools.testing_tools as test_utils
from tests.test_data import QUALTRICS_TEST_OBJECTS, TEST_RESPONSE_DICT, ARBITRARY_UUID


class BaseSurveyTestCase(test_utils.BaseTestCase):
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


class TestSurveyClient(BaseSurveyTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.survey_client = ep.SurveyClient(cls.test_survey_id)

    def test_sc_01_get_response_ok(self):
        response = self.survey_client.get_response(self.test_response_id)
        self.assertCountEqual(QUALTRICS_TEST_OBJECTS['unittest-survey-1']['export_tags'], list(response.keys()))

    def test_sc_02_get_response_ok_omit_null_values(self):
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


class TestSurveyResponse(BaseSurveyTestCase):

    def test_sr_01_init_ok(self):
        rd = copy.deepcopy(TEST_RESPONSE_DICT)
        survey_response = ep.SurveyResponse(response_dict=rd)
        self.assertIsInstance(survey_response, ep.SurveyResponse)

    def test_sr_02_init_fail_invalid_uuid(self):
        for required_uuid_param in ['project_task_id', 'anon_project_specific_user_id', 'anon_user_task_id']:
            rd = copy.deepcopy(TEST_RESPONSE_DICT)
            rd[required_uuid_param] = 'this-is-not-a-valid-uuid'
            with self.assertRaises(utils.DetailedValueError) as context:
                ep.SurveyResponse(response_dict=rd)
            err = context.exception
            err_msg = err.args[0]
            self.assertEqual('invalid uuid', err_msg)

    def test_sr_03_init_fail_missing_required_attribute(self):
        for required_param in list(TEST_RESPONSE_DICT.keys()):
            rd = copy.deepcopy(TEST_RESPONSE_DICT)
            self.logger.debug(f'Working on required_param {required_param}', extra={'response_dict': rd})
            del rd[required_param]
            with self.assertRaises(utils.DetailedValueError) as context:
                ep.SurveyResponse(response_dict=rd)
            err = context.exception
            err_msg = err.args[0]
            self.assertIn(err_msg, [f'Required parameter {required_param} not present in body of call', 'invalid uuid'])

    def test_sr_04_init_fail_required_attribute_is_an_empty_string(self):
        for required_param in list(TEST_RESPONSE_DICT.keys()):
            rd = copy.deepcopy(TEST_RESPONSE_DICT)
            rd[required_param] = ''
            with self.assertRaises(utils.DetailedValueError) as context:
                ep.SurveyResponse(response_dict=rd)
            err = context.exception
            err_msg = err.args[0]
            self.assertIn(err_msg, [f'Required parameter {required_param} not present in body of call', 'invalid uuid'])

    def test_sr_05_check_project_task_exists_ok(self):
        rd = copy.deepcopy(TEST_RESPONSE_DICT)
        survey_response = ep.SurveyResponse(response_dict=rd)
        self.assertTrue(survey_response.check_project_task_exists())

    def test_sr_06_check_project_task_exists_fail(self):
        rd = copy.deepcopy(TEST_RESPONSE_DICT)
        rd['project_task_id'] = ARBITRARY_UUID
        survey_response = ep.SurveyResponse(response_dict=rd)
        with self.assertRaises(utils.ObjectDoesNotExistError) as context:
            survey_response.check_project_task_exists()
        err = context.exception
        err_msg = err.args[0]
        self.assertEqual(f'Project tasks id {ARBITRARY_UUID} not found in Thiscovery database', err_msg)

    def test_sr_07_put_item_ok(self):
        rd = copy.deepcopy(TEST_RESPONSE_DICT)
        survey_response = ep.SurveyResponse(response_dict=rd)
        ddb_response = survey_response.put_item()
        self.assertEqual(HTTPStatus.OK, ddb_response['ResponseMetadata']['HTTPStatusCode'])

    def test_sr_08_put_responses_api_ok(self):
        rd = copy.deepcopy(TEST_RESPONSE_DICT)
        expected_status = HTTPStatus.NO_CONTENT
        result = test_utils.test_put(
            local_method=ep.put_response_api,
            aws_url="v1/response",
            request_body=json.dumps(rd),
        )
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)


class TestEndpoints(BaseSurveyTestCase):
    retrieve_responses_endpoint = 'v1/response'

    def test_ep_01_retrieve_response_api_ok(self):
        params = {
            'survey_id': self.test_survey_id,
            'response_id': self.test_response_id,
            'question_ids': json.dumps(self.test_question_ids)
        }
        result = test_utils.test_get(
            local_method=ep.retrieve_responses_api,
            aws_url=self.retrieve_responses_endpoint,
            querystring_parameters=params,
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
        pprint(json.loads(result['body']))
        self.assertCountEqual(expected_result_body, json.loads(result['body']))

    def test_ep_02_retrieve_response_api_ok_question_ids_not_specified(self):
        params = {
            'survey_id': self.test_survey_id,
            'response_id': self.test_response_id,
        }
        result = test_utils.test_get(
            local_method=ep.retrieve_responses_api,
            aws_url=self.retrieve_responses_endpoint,
            querystring_parameters=params,
        )
        self.assertEqual(HTTPStatus.OK, result['statusCode'])
        expected_result_body_keys = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['export_tags']

        self.assertCountEqual(expected_result_body_keys, json.loads(result['body']).keys())


class TestGetInterviewQuestions(test_utils.BaseTestCase):
    interview_questions_endpoint = 'v1/interview-questions'

    def test_get_interview_questions_ok(self):
        path_parameters = {
            'id': 'SV_eDrjXPqGElN0Mwm'
        }
        expected_status = HTTPStatus.OK

        result = test_utils.test_get(ep.get_interview_questions_api, self.interview_questions_endpoint, path_parameters=path_parameters)
        result_status = result['statusCode']
        result_body = json.loads(result['body'])

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        import time
        time.sleep(1)
        pprint(result_body)
        time.sleep(1)

