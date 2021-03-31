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

import src.common.constants as const
import src.endpoints as ep
import tests.test_data as td


class TestGetInterviewQuestions(test_utils.BaseTestCase):
    interview_questions_endpoint = "v1/interview-questions"

    def test_get_interview_questions_ok(self):
        path_parameters = {"id": "SV_eDrjXPqGElN0Mwm"}
        expected_status = HTTPStatus.OK
        expected_body = {
            "blocks": [
                {
                    "block_id": "BL_eQESIsA5b3xfWn3",
                    "block_name": "Introductory questions",
                    "questions": [
                        {
                            "question_description": "<p>Please take a minute "
                            "to reflect on how you "
                            "feel and/or things you "
                            "are grateful for this "
                            "morning.</p>",
                            "question_id": "QID1",
                            "question_name": "Q1",
                            "question_text": "<h3>How are you this " "morning?</h3>",
                            "sequence_no": "1",
                        },
                        {
                            "question_description": "<p>Are you planning to "
                            "bake cakes? Going on a "
                            "bike ride? Maybe going on "
                            "a bike ride and then "
                            "eating cake? Whatever "
                            "your plans are, please "
                            "don't be shy to "
                            "share.</p>",
                            "question_id": "QID2",
                            "question_name": "Q2",
                            "question_text": "<h3>What are you planning to do "
                            "this afternoon?</h3>",
                            "sequence_no": "2",
                        },
                    ],
                },
                {
                    "block_id": "BL_3qH1dnbq50y9V0a",
                    "block_name": "Your experience using thiscovery",
                    "questions": [
                        {
                            "question_description": None,
                            "question_id": "QID3",
                            "question_name": "Q3",
                            "question_text": "<h3>How many thiscovery tasks "
                            "have you completed to date?</h3>",
                            "sequence_no": "3",
                        },
                        {
                            "question_description": "<p>If you enjoyed using "
                            "thiscovery, why not "
                            "spread the word?</p>",
                            "question_id": "QID4",
                            "question_name": "Q4",
                            "question_text": "<h3>Would you recommend "
                            "thiscovery to a friend?</h3>",
                            "sequence_no": "4",
                        },
                    ],
                },
            ],
            "count": 4,
            "modified": "2021-02-16T16:36:15Z",
            "survey_id": "SV_eDrjXPqGElN0Mwm",
        }

        result = test_utils.test_get(
            ep.get_interview_questions_api,
            self.interview_questions_endpoint,
            path_parameters=path_parameters,
        )
        result_status = result["statusCode"]
        result_body = json.loads(result["body"])

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_body, result_body)

    def test_get_interview_questions_not_found(self):
        path_parameters = {"id": "SV_NonExistent1234"}
        expected_status = HTTPStatus.NOT_FOUND
        result = test_utils.test_get(
            ep.get_interview_questions_api,
            self.interview_questions_endpoint,
            path_parameters=path_parameters,
        )
        result_status = result["statusCode"]
        self.assertEqual(expected_status, result_status)


class TestPutInterviewQuestions(test_utils.BaseTestCase):
    def test_put_interview_questions_ok(self):
        test_event = copy.deepcopy(td.TEST_INTERVIEW_QUESTIONS_UPDATED_EB_EVENT)
        result = ep.put_interview_questions(test_event, None)
        self.assertEqual(HTTPStatus.OK, result["statusCode"])
        updated_question_ids, deleted_question_ids = json.loads(result["body"])
        self.assertEqual(4, len(updated_question_ids))

    def test_put_interview_questions_from_THIS_account_ok(self):
        test_event = copy.deepcopy(
            td.TEST_INTERVIEW_QUESTIONS_UPDATED_ON_THIS_ACCOUNT_EB_EVENT
        )
        result = ep.put_interview_questions(test_event, None)
        self.assertEqual(HTTPStatus.OK, result["statusCode"])
        updated_question_ids, deleted_question_ids = json.loads(result["body"])
        self.assertEqual(4, len(updated_question_ids))

    def test_put_interview_missing_account_info(self):
        test_event = copy.deepcopy(td.TEST_INTERVIEW_QUESTIONS_UPDATED_EB_EVENT)
        del test_event["detail"]["account"]
        with self.assertRaises(utils.DetailedValueError):
            ep.put_interview_questions(test_event, None)

    def test_put_interview_missing_survey_id(self):
        test_event = copy.deepcopy(td.TEST_INTERVIEW_QUESTIONS_UPDATED_EB_EVENT)
        del test_event["detail"]["survey_id"]
        with self.assertRaises(utils.DetailedValueError):
            ep.put_interview_questions(test_event, None)

    def test_put_interview_question_missing_div_of_class_prompt(self):
        test_event = copy.deepcopy(td.TEST_INTERVIEW_QUESTIONS_UPDATED_EB_EVENT)
        test_event["detail"]["survey_id"] = "SV_0lKExcIYn4ax4h0"
        with self.assertRaises(utils.DetailedValueError):
            ep.put_interview_questions(test_event, None)

    def test_deletion_of_questions_no_longer_in_survey_definition(self):
        mock_deleted_question = {
            "block_id": "BL_3qH1dnbq50y9V0a",
            "block_name": "Your experience using thiscovery",
            "question_description": "<p>Take a moment to reflect on how much you like bread before answering this question.</p>",
            "question_id": "QID12",
            "question_name": "Q12",
            "question_text": "<h3>Is thiscovery the best invention since sliced bread?</h3>",
            "sequence_no": "12",
            "survey_id": "SV_eDrjXPqGElN0Mwm",
            "survey_modified": "2021-02-16T15:59:12Z",
        }
        ddb_client = Dynamodb(stack_name=const.STACK_NAME)
        ddb_client.put_item(
            table_name=const.INTERVIEW_QUESTIONS_TABLE["name"],
            key=mock_deleted_question["survey_id"],
            item_type="interview_question",
            item_details=None,
            item=mock_deleted_question,
            update_allowed=True,
            key_name=const.INTERVIEW_QUESTIONS_TABLE["partition_key"],
            sort_key={
                const.INTERVIEW_QUESTIONS_TABLE["sort_key"]: mock_deleted_question[
                    "question_id"
                ]
            },
        )
        test_event = copy.deepcopy(td.TEST_INTERVIEW_QUESTIONS_UPDATED_EB_EVENT)
        result = ep.put_interview_questions(test_event, None)
        self.assertEqual(HTTPStatus.OK, result["statusCode"])
        updated_question_ids, deleted_question_ids = json.loads(result["body"])
        self.assertEqual(4, len(updated_question_ids))
        self.assertEqual([mock_deleted_question["question_id"]], deleted_question_ids)
