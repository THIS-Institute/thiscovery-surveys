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
from thiscovery_lib.qualtrics import SurveyDefinitionsClient


class SurveyDefinition:

    def __init__(self, qualtrics_account_name='cambridge', survey_id=None, correlation_id=None):
        client = SurveyDefinitionsClient(
            qualtrics_account_name=qualtrics_account_name,
            survey_id=survey_id,
            correlation_id=correlation_id,
        )
        response = client.get_survey()
        assert response['meta']['httpStatus'] == '200 - OK', f'Call to Qualtrics API failed with response {response}'
        self.definition = response['result']

    def get_interview_question_list(self):
        #todo: implement this
        pass


