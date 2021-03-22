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
import local.dev_config
import local.secrets
import json
import thiscovery_lib.qualtrics as qualtrics
import thiscovery_lib.utilities as utils

from http import HTTPStatus
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.events_api_utilities import EventsApiClient
from thiscovery_lib.qualtrics import DistributionsClient

import common.constants as const
from common.survey_response import SurveyClient, SurveyResponse
from common.survey_definition import SurveyDefinition
from common.task_responses import TaskResponse
from consent import ConsentEvent
from interview_tasks import InterviewTask, UserInterviewTask


class DistributionLinksGenerator:

    def __init__(self, survey_id, contact_list_id, project_task_id=None):
        self.survey_id = survey_id
        self.contact_list_id = contact_list_id
        self.dist_client = qualtrics.DistributionsClient()
        self.ddb_client = Dynamodb(stack_name=const.STACK_NAME)
        self.project_task_id = project_task_id
        # ImportManager.check_project_task_exists(self.project_task_id)

    def generate_links_and_upload_to_dynamodb(self):
        r = self.dist_client.create_individual_links(survey_id=self.survey_id, contact_list_id=self.contact_list_id)
        distribution_id = r['result']['id']
        r = self.dist_client.list_distribution_links(distribution_id, self.survey_id)
        rows = r['result']['elements']
        for row in rows:
            self.ddb_client.put_item(
                table_name=const.PERSONAL_LINKS_TABLE,
                key=self.survey_id,
                item_type='personal survey link',
                item_details=dict(),
                item={
                    'status': 'new',
                },
                key_name='survey_id',
                sort_key={
                    'url': row['link'],
                }
            )


def create_links():
    dlg = DistributionLinksGenerator('SV_8nPQROmmrkovcNv', 'ML_6ifLPwSfjagoQ3H')
    dlg.generate_links_and_upload_to_dynamodb()


if __name__ == '__main__':
    create_links()
