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


class PersonalLinkManager:

    def __init__(self, survey_id, user_id, correlation_id=None):
        self.acc_survey_id = survey_id
        self.user_id = user_id
        self.correlation_id = correlation_id
        if correlation_id is None:
            self.correlation_id = utils.get_correlation_id()

        self.ddb_client = Dynamodb(
            stack_name=const.STACK_NAME,
            correlation_id=self.correlation_id
        )

    def get_personal_link(self):
        item = self.ddb_client.get_item(
            table_name=const.PERSONAL_LINKS_TABLE,
            key=self.acc_survey_id,
            key_name='survey_id',
            sort_key={'user_id': self.user_id},
        )
        try:
            return item['url']
        except TypeError:  # item is None; get unassigned links and assign one to user
            unassigned_links = self.ddb_client.query(
                table_name=const.PERSONAL_LINKS_TABLE,
                IndexName='unassigned-links',
                KeyConditionExpression='survey_id = :survey_id '
                                       'AND status = :status',
                ExpressionAttributeValues={
                    ':survey_id': self.acc_survey_id,
                    ':status': 'new',
                }
            )
            unassigned_links_len = len(unassigned_links)
            if not unassigned_links:
                pass  # todo: create new links (sync)
            elif unassigned_links_len <= const.PERSONAL_LINKS_BUFFER:
                pass  # todo: create new links (async)
            else:
                unassigned_links.sort(key=lambda x: x['expires'])
                user_link = unassigned_links[0]
                # todo: update ddb link row to assigned
                return user_link['url']


def create_links():
    dlg = DistributionLinksGenerator('SV_8nPQROmmrkovcNv', 'ML_6ifLPwSfjagoQ3H')
    dlg.generate_links_and_upload_to_dynamodb()


@utils.lambda_wrapper
@utils.api_error_handler
def get_personal_link_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    params = event['queryStringParameters']
    survey_id = params['survey_id']
    user_id = str(utils.validate_uuid(params['user_id']))
    logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'survey_id': survey_id})
    plm = PersonalLinkManager(survey_id, user_id)
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(plm.get_personal_link())
    }


if __name__ == '__main__':
    create_links()
