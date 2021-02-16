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
from interview_tasks import UserInterviewTask

import tests.test_data as td


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
