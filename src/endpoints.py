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
import json
import thiscovery_lib.utilities as utils

from http import HTTPStatus
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.qualtrics import ResponsesClient

import common.constants as const
import common.task_responses as tr
from consent import ConsentEvent
from interview_tasks import UserInterviewTask


class SurveyResponse:
    responses_table = 'Responses'

    def __init__(self, response_dict, correlation_id=None):
        self.survey_id = response_dict.pop('survey_id', None)
        self.response_id = response_dict.pop('response_id', None)
        self.project_task_id = str(utils.validate_uuid(response_dict.pop('project_task_id', None)))
        self.anon_project_specific_user_id = str(utils.validate_uuid(response_dict.pop('anon_project_specific_user_id', None)))
        self.anon_user_task_id = str(utils.validate_uuid(response_dict.pop('anon_user_task_id', None)))
        for required_parameter_name, value in [('survey_id', self.survey_id), ('response_id', self.response_id)]:
            if not value:
                raise utils.DetailedValueError(f'Required parameter {required_parameter_name} not present in body of call',
                                               details={'response_dict': response_dict, 'correlation_id': correlation_id})
        self.response_dict = response_dict
        self.ddb_client = Dynamodb(
            stack_name=const.STACK_NAME,
            correlation_id=correlation_id,
        )
        self.correlation_id = correlation_id

    def check_project_task_exists(self):
        env_name = utils.get_environment_name()
        if env_name == 'prod':
            core_api_url = 'https://api.thiscovery.org/'
        else:
            core_api_url = f'https://{env_name}-api.thiscovery.org/'
        result = utils.aws_get(
            endpoint_url='v1/project',
            base_url=core_api_url,
        )
        assert result['statusCode'] == HTTPStatus.OK, f'Call to core API returned error: {result}'
        projects = json.loads(result['body'])
        project_task_ids = list()
        for p in projects:
            tasks = p['tasks']
            for t in tasks:
                project_task_ids.append(t['id'])
        if self.project_task_id not in project_task_ids:
            raise utils.ObjectDoesNotExistError(f'Project tasks id {self.project_task_id} not found in Thiscovery database',
                                                details={'project_task_ids': project_task_ids, 'correlation_id': self.correlation_id})
        return True

    def put_item(self):
        return self.ddb_client.put_item(
            table_name=self.responses_table,
            key=f'{self.survey_id}-{self.response_id}',
            item_type='survey_response',
            item_details={
                **self.response_dict,
                'correlation_id': self.correlation_id
            },
            item={
                'survey_id': self.survey_id,
                'response_id': self.response_id,
                'project_task_id': self.project_task_id,
                'anon_project_specific_user_id': self.anon_project_specific_user_id,
                'anon_user_task_id': self.anon_user_task_id,
            },
            update_allowed=True,
        )


class SurveyClient:
    def __init__(self, survey_id, correlation_id=None):
        self.survey_id = survey_id
        self.correlation_id = correlation_id
        self.responses_client = ResponsesClient(survey_id=survey_id, correlation_id=correlation_id)
        self.responses_schema = self.responses_client.retrieve_survey_response_schema()
        # self.export_tags_to_question_ids = {v['exportTag']: k for k, v in self.responses_schema['result']['properties']['values']['properties'].items()}
        self.question_ids_to_export_tags = {k: v['exportTag'] for k, v in self.responses_schema['result']['properties']['values']['properties'].items()}

    def get_response(self, response_id, export_tags=None, return_nulls=True):
        """

        Args:
            response_id:
            export_tags (list): List of question ids (as displayed in a Qualtrics data export) to retrieve responses for.
                                If None, all questions will be included in response
            return_nulls (bool): If True, return body includes export tags of null responses

        Returns:
            Dictionary containing export_tag, response_value pairs for each survey question
        """
        r = self.responses_client.retrieve_response(response_id=response_id)
        values_dict_by_id = r['result']['values']
        values_dict_by_export_tag = {self.question_ids_to_export_tags[k]: v for k, v in values_dict_by_id.items()}

        if return_nulls is True:
            for _, v in self.question_ids_to_export_tags.items():
                if v not in values_dict_by_export_tag.keys():
                    values_dict_by_export_tag[v] = None

        if export_tags is not None:
            values_dict_by_export_tag = {k: v for k, v in values_dict_by_export_tag.items() if k in export_tags}
        return values_dict_by_export_tag


@utils.lambda_wrapper
@utils.api_error_handler
def raise_error_api(event, context):
    import time
    logger = event['logger']
    correlation_id = event['correlation_id']

    params = event['queryStringParameters']
    error_id = params['error_id']
    logger.info('API call', extra={'error_id': error_id, 'correlation_id': correlation_id, 'event': event})

    errorjson = {'error_id': error_id, 'correlation_id': str(correlation_id)}
    msg = 'no error'

    if error_id == '4xx':
        msg = 'error triggered for testing purposes'
        raise utils.ObjectDoesNotExistError(msg, errorjson)
    elif error_id == '5xx':
        msg = 'error triggered for testing purposes'
        raise Exception(msg)
    elif error_id == 'slow':
        msg = 'slow response triggered for testing purposes'
        time.sleep(2)  # this should trigger lambda duration alarm
    elif error_id == 'timeout':
        msg = 'timeout response triggered for testing purposes'
        time.sleep(10)  # this should trigger lambda timeout

    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(msg)
    }


@utils.lambda_wrapper
@utils.api_error_handler
def retrieve_responses_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    parameters = event['queryStringParameters']
    logger.info('API call', extra={
        'parameters': parameters,
        'correlation_id': correlation_id,
    })
    survey_id = parameters.get('survey_id')
    response_id = parameters.get('response_id')
    question_ids = parameters.get('question_ids')
    if question_ids:
        question_ids = json.loads(question_ids)
    survey_client = SurveyClient(survey_id=survey_id, correlation_id=correlation_id)
    response_body = survey_client.get_response(response_id=response_id, export_tags=question_ids)
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(response_body),
    }


@utils.lambda_wrapper
@utils.api_error_handler
def put_response_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    body_dict = json.loads(event['body'])
    logger.info('API call', extra={
        'body_dict': body_dict,
        'correlation_id': correlation_id,
        'event': event
    })
    alarm_test = body_dict.get('brew_coffee')
    if alarm_test:
        raise utils.DeliberateError('Coffee is not available', details={})
    survey_response = SurveyResponse(response_dict=body_dict, correlation_id=correlation_id)
    survey_response.check_project_task_exists()
    ddb_response = survey_response.put_item()
    logger.debug('Dynamodb response', extra={
        'ddb_response': ddb_response,
        'correlation_id': correlation_id,
    })
    return {
        "statusCode": HTTPStatus.NO_CONTENT
    }


@utils.lambda_wrapper
@utils.api_error_handler
def send_consent_email_api(event, context):
    consent_event = ConsentEvent(survey_consent_event=event)
    dump_result, notification_result = consent_event.parse()
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(
            {
                'store_result': dump_result,
                'notification_result': notification_result,
            }
        )
    }


@utils.lambda_wrapper
def put_task_response(event, context):
    pass


@utils.lambda_wrapper
def put_user_interview_task(event, context):
    uit = UserInterviewTask(event=event)
    uit.get_interview_task()
    uit.ddb_dump()
    return {"statusCode": HTTPStatus.OK, "body": json.dumps('')}


@utils.lambda_wrapper
@utils.api_error_handler
def get_user_interview_task_api(event, context):
    pass
