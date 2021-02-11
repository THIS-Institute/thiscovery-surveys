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

test_user_interview_task_event = {
    "detail-type": "user_interview_task",
    "detail": {
        "anon_project_specific_user_id": "5e954b5f-2363-406d-bba8-d2bedee511d4",
        "anon_user_task_id": "3dce6e9c-9b20-4d7f-a266-9967553dbc16",
        "interview_task_id": "796e49f1-64e1-4019-aef2-84f5ffe7e69c",
        "response_id": "SV_b8jGMAQJjUfsIVU-R_1rGorZ2GxFDwdD9"
    },
    "id": "67cac63b-8941-3a10-807e-bc9a8c8dffba",
    "time": "2021-02-11 15:05:11.501700+00:00",
    "type": "thiscovery_event"
}


class TestUserInterviewTask(test_utils.BaseTestCase):

    def test_init_ok(self):
        uit = UserInterviewTask(event=test_user_interview_task_event)
        self.assertEqual('SV_b8jGMAQJjUfsIVU-R_1rGorZ2GxFDwdD9', uit._response_id)

    def test_get_interview_task_ok(self):
        uit = UserInterviewTask(event=test_user_interview_task_event)
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
        ]
        self.assertCountEqual(interview_task_keys, list(uit.interview_task.keys()))
