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
import unittest
from http import HTTPStatus
from pprint import pprint
from thiscovery_lib.dynamodb_utilities import Dynamodb

import src.common.constants as const
import src.endpoints as ep
import tests.test_data as td
from src.common.survey_definition import SurveyDefinition
from src.interview_tasks import InterviewTask, UserInterviewTask
from tests.test_data import QUALTRICS_TEST_OBJECTS, TEST_RESPONSE_DICT, ARBITRARY_UUID


class TestSurveyDefinition(test_utils.BaseTestCase):

    def test_ddb_load_interview_questions(self):
        test_survey_id = copy.deepcopy(td.TEST_INTERVIEW_QUESTIONS_UPDATED_EB_EVENT['detail']['survey_id'])
        sd = SurveyDefinition(survey_id=test_survey_id)
        pprint(sd.ddb_load_interview_questions())
