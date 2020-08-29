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
import unittest

import src.common.qualtrics as qualtrics
from tests.test_data import QUALTRICS_TEST_OBJECTS
from thiscovery_lib.utilities import set_running_unit_tests


class TestResponsesClient(unittest.TestCase):
    test_survey_id = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id']
    test_response_id = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['response_1_id']

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        cls.responses_client = qualtrics.ResponsesClient(cls.test_survey_id)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_responses_01_retrieve_response_ok(self):
        response = self.responses_client.retrieve_response(response_id=self.test_response_id)
        self.assertEqual('200 - OK', response['meta']['httpStatus'])
        expected_result = {
            'displayedFields': ['QID1',
                                'QID7_TEXT',
                                'QID3',
                                'QID2',
                                'QID5_TEXT',
                                'QID8_TEXT',
                                'QID4',
                                'QID6_TEXT'],
            'displayedValues': {'QID1': [1, 2],
                                'QID2': [1, 2],
                                'QID3': [1, 2],
                                'QID4': [1, 2]},
            'labels': {'QID1': 'yes',
                       'QID1_DO': ['yes', 'no'],
                       'QID2': 'no',
                       'QID2_DO': ['yes', 'no'],
                       'QID3': 'yes',
                       'QID3_DO': ['yes', 'no'],
                       'QID4': 'no',
                       'QID4_DO': ['yes', 'no'],
                       'finished': 'True',
                       'status': 'IP Address'},
            'responseId': 'R_1BziZVeffoDpTQl',
            'values': {'QID1': 1,
                       'QID1_DO': ['1', '2'],
                       'QID2': 2,
                       'QID2_DO': ['1', '2'],
                       'QID3': 1,
                       'QID3_DO': ['1', '2'],
                       'QID4': 2,
                       'QID4_DO': ['1', '2'],
                       'QID5_TEXT': 'Much better.',
                       'QID6_TEXT': 'Much worse.',
                       'distributionChannel': 'anonymous',
                       'duration': 25,
                       'endDate': '2020-08-24T17:42:45Z',
                       'finished': 1,
                       'progress': 100,
                       'recordedDate': '2020-08-24T17:42:46.146Z',
                       'startDate': '2020-08-24T17:42:20Z',
                       'status': 0,
                       'userLanguage': 'EN-GB'}}
        result = response['result']
        # strip PID
        del result['values']['ipAddress']
        del result['values']['locationLatitude']
        del result['values']['locationLongitude']
        self.assertCountEqual(expected_result, result)

    def test_responses_02_retrieve_schema_ok(self):
        response = self.responses_client.retrieve_survey_response_schema()
        self.assertEqual('200 - OK', response['meta']['httpStatus'])
        expected_values_properties_keys = ['QID1', 'QID10_1', 'QID10_13', 'QID10_15', 'QID10_16', 'QID10_17', 'QID10_18', 'QID10_30', 'QID10_4', 'QID10_DO', 'QID11', 'QID11_8_TEXT', 'QID11_DO', 'QID12', 'QID12_12_TEXT', 'QID12_DO', 'QID1_DO', 'QID2', 'QID2_DO', 'QID3', 'QID3_DO', 'QID4', 'QID4_DO', 'QID5_DO', 'QID5_TEXT', 'QID6_DO', 'QID6_TEXT', 'QID7_DO', 'QID7_TEXT', 'QID8_DO', 'QID8_TEXT', 'distributionChannel', 'duration', 'endDate', 'externalDataReference', 'finished', 'ipAddress', 'locationLatitude', 'locationLongitude', 'progress', 'recipientEmail', 'recipientFirstName', 'recipientLastName', 'recordedDate', 'startDate', 'status', 'userLanguage']
        self.assertCountEqual(expected_values_properties_keys, response['result']['properties']['values']['properties'].keys())
