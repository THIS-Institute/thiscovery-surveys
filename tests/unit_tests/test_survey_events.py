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
import thiscovery_dev_tools.testing_tools as test_tools
import thiscovery_lib.utilities as utils
from http import HTTPStatus
from pprint import pprint

import src.endpoints as ep
import src.common.constants as const
import tests.test_data as td
import tests.testing_utilities as test_utils


class TestUserAgent(test_tools.BaseTestCase, test_utils.DdbMixin):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clear_task_responses_table()

    def test_put_user_agent_data_ok(self):
        test_event = copy.deepcopy(td.TEST_SURVEY_USER_AGENT_EB_EVENT)
        result = ep.put_user_agent_data(test_event, None)
        self.assertEqual(HTTPStatus.OK, result['statusCode'])
        items = self.ddb_client.scan(table_name=const.TASK_RESPONSES_TABLE['name'])
        self.assertEqual(1, len(items))
        expected_item = {
            'anon_project_specific_user_id': '7e6e4bca-4f0b-4f71-8660-790c1baf3b11',
            'anon_user_task_id': '2035dce9-9745-46cc-8db0-3e8de47c463b',
            'browser_type': 'Firefox',
            'browser_version': '86.0',
            'details': {},
            'event_time': '2021-03-02T21:46:18Z',
            'os': 'Ubuntu',
            'project_task_id': 'b335c46a-bc1b-4f3d-ad0f-0b8d0826a908',
            'response_id': 'SV_b8jGMAQJjUfsIVU-R_27PS3xFkIH36j29',
            'screen_resolution': '1280x1024',
            'type': 'survey_user_agent',
            'user_agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'
        }
        item = items[0]
        del item['created']
        del item['modified']
        self.assertDictEqual(expected_item, item)
