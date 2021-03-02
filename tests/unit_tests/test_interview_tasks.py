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

import src.endpoints as ep
import src.common.constants as const
import tests.test_data as td
from interview_tasks import InterviewTask, UserInterviewTask
from tests.testing_utilities import DdbMixin


class TestUserInterviewTask(test_utils.BaseTestCase):

    def test_init_from_event_ok(self):
        uit = UserInterviewTask.from_eb_event(event=copy.deepcopy(td.TEST_USER_INTERVIEW_TASK_EB_EVENT))
        self.assertEqual(td.TEST_USER_INTERVIEW_TASK_EB_EVENT['detail']['response_id'], uit._response_id)

    def test_init_from_event_missing_anon_project_specific_user_id(self):
        test_event = copy.deepcopy(td.TEST_USER_INTERVIEW_TASK_EB_EVENT)
        del test_event['detail']['anon_project_specific_user_id']
        with self.assertRaises(utils.DetailedValueError):
            UserInterviewTask.from_eb_event(event=test_event)

    def test_init_from_event_missing_anon_user_task_id(self):
        test_event = copy.deepcopy(td.TEST_USER_INTERVIEW_TASK_EB_EVENT)
        del test_event['detail']['anon_user_task_id']
        with self.assertRaises(utils.DetailedValueError):
            UserInterviewTask.from_eb_event(event=test_event)

    def test_get_interview_task_ok(self):
        uit = UserInterviewTask.from_eb_event(event=copy.deepcopy(td.TEST_USER_INTERVIEW_TASK_EB_EVENT))
        uit.get_interview_task()
        interview_task_keys = [
            'appointment_type_id',
            'completion_url',
            'description',
            'details',
            'interview_task_id',
            'live_available',
            'live_survey_id',
            'name',
            'on_demand_available',
            'on_demand_survey_id',
            'project_task_id',
            'short_name',
            'type',
            'modified',
        ]
        self.assertCountEqual(interview_task_keys, list(uit.interview_task.keys()))


class TestUserInterviewTaskEndpoint(test_utils.BaseTestCase, DdbMixin):
    entity_base_url = 'v1/user-interview-tasks'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clear_task_responses_table()
        uit = UserInterviewTask(**td.TEST_USER_INTERVIEW_TASK)
        uit.get_interview_task()
        uit.ddb_dump()

    def test_get_user_interview_task_ok(self):
        path_parameters = {
            'id': td.TEST_USER_INTERVIEW_TASK['response_id']
        }
        expected_status = HTTPStatus.OK

        result = test_utils.test_get(ep.get_user_interview_task_api, self.entity_base_url, path_parameters=path_parameters)
        result_status = result['statusCode']
        result_body = json.loads(result['body'])
        result_it = result_body.pop('interview_task')
        del result_it['modified']
        self.assertEqual(expected_status, result_status)
        expected_body = copy.deepcopy(td.TEST_USER_INTERVIEW_TASK)
        del expected_body['detail_type']
        self.assertEqual(expected_body, result_body)
        self.assertEqual(td.TEST_INTERVIEW_TASK, result_it)

    def test_get_user_interview_task_does_not_exist(self):
        path_parameters = {
            'id': td.TEST_USER_INTERVIEW_TASK['response_id'].replace('2', '3')
        }
        expected_status = HTTPStatus.NOT_FOUND
        result = test_utils.test_get(ep.get_user_interview_task_api, self.entity_base_url, path_parameters=path_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

    def test_put_user_interview_task_ok(self):
        self.clear_task_responses_table()
        test_event = copy.deepcopy(td.TEST_USER_INTERVIEW_TASK_EB_EVENT)
        result = ep.put_user_interview_task(test_event, None)
        self.assertEqual(HTTPStatus.OK, result['statusCode'])
        items = self.ddb_client.scan(table_name=const.TASK_RESPONSES_TABLE['name'])
        self.assertEqual(1, len(items))
        expected_item = {
            'anon_project_specific_user_id': '7e6e4bca-4f0b-4f71-8660-790c1baf3b11',
            'anon_user_task_id': '2035dce9-9745-46cc-8db0-3e8de47c463b',
            'details': {
                'event_type': 'user_interview_task'
            },
            'event_time': '2021-02-12T10:57:09Z',
            'interview_task': {
                'appointment_type_id': '448161419',
                'completion_url': 'https://www.thiscovery.org/',
                'description': 'Questions about PSFU-06-A',
                'details': None,
                'interview_task_id': '0fda6eff-b1e5-44df-93b4-3d71c03adeff',
                'live_available': True,
                'live_survey_id': 'SV_eDrjXPqGElN0Mwm',
                'name': 'PSFU-06-A interview for healthcare professionals',
                'on_demand_available': False,
                'on_demand_survey_id': None,
                'project_task_id': 'b335c46a-bc1b-4f3d-ad0f-0b8d0826a908',
                'short_name': 'PSFU-06-A hcp interview',
                'type': 'interview_task'
            },
            'interview_task_id': '0fda6eff-b1e5-44df-93b4-3d71c03adeff',
            'project_task_id': 'b335c46a-bc1b-4f3d-ad0f-0b8d0826a908',
            'response_id': 'SV_b8jGMAQJjUfsIVU-R_27PS3xFkIH36j29',
            'type': 'user_interview_task'}
        item = items[0]
        del item['created']
        del item['modified']
        del item['interview_task']['modified']
        self.assertDictEqual(expected_item, item)

    def test_put_user_interview_task_missing_task_id(self):
        test_event = copy.deepcopy(td.TEST_USER_INTERVIEW_TASK_EB_EVENT)
        del test_event['detail']['interview_task_id']
        with self.assertRaises(utils.DetailedValueError):
            ep.put_user_interview_task(test_event, None)


class TestInterviewTaskEndpoint(test_utils.BaseTestCase):
    entity_base_url = 'v1/interview-tasks'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ddb_client = Dynamodb(stack_name=const.STACK_NAME)
        cls.ddb_client.delete_all(
            table_name=const.INTERVIEW_TASKS_TABLE['name'],
            key_name=const.INTERVIEW_TASKS_TABLE['partition_key'],
            sort_key_name=const.INTERVIEW_TASKS_TABLE['sort_key'],
        )
        test_it = InterviewTask(**td.TEST_INTERVIEW_TASK)
        test_it.ddb_dump()

    def test_get_interview_task_ok(self):
        path_parameters = {
            'id': td.TEST_INTERVIEW_TASK['interview_task_id']
        }
        expected_status = HTTPStatus.OK
        result = test_utils.test_get(ep.get_interview_task_api, self.entity_base_url, path_parameters=path_parameters)
        result_status = result['statusCode']
        result_body = json.loads(result['body'])
        del result_body['modified']
        self.assertEqual(expected_status, result_status)
        self.assertEqual(td.TEST_INTERVIEW_TASK, result_body)

    def test_get_interview_task_not_found(self):
        path_parameters = {
            'id': td.ARBITRARY_UUID
        }
        expected_status = HTTPStatus.NOT_FOUND
        result = test_utils.test_get(ep.get_interview_task_api, self.entity_base_url, path_parameters=path_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)
