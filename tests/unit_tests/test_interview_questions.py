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
from thiscovery_lib.qualtrics import SurveyDefinitionsClient

import thiscovery_lib.utilities as utils
import src.endpoints as ep
import thiscovery_dev_tools.testing_tools as test_utils
from common.survey_definition import SurveyDefinition
from tests.test_data import QUALTRICS_TEST_OBJECTS, TEST_RESPONSE_DICT, ARBITRARY_UUID


class TestInterviewQuestions(test_utils.BaseTestCase):

    def test_get_interview_questions_api_ok(self):
        import time
        sdc = SurveyDefinitionsClient(survey_id='SV_eDrjXPqGElN0Mwm')
        time.sleep(1)
        pprint(sdc.get_survey())
        time.sleep(1)

    def test_temp(self):
        sd = SurveyDefinition(survey_id='SV_eDrjXPqGElN0Mwm')
        sd.ddb_dump_interview_questions()
