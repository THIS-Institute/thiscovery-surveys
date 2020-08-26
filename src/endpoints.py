import json
from http import HTTPStatus

import common.utilities as utils
from common.dynamodb_utilities import Dynamodb
from common.qualtrics import ResponsesClient


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
        self.ddb_client = Dynamodb(correlation_id=correlation_id)
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
            key=f'{self.survey_id}_{self.response_id}',
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
            return_nulls (bool): If True, return body includes export tags of null responses

        Returns:
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
def retrieve_responses_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    body_dict = json.loads(event['body'])
    logger.info('API call', extra={
        'body_dict': body_dict,
        'correlation_id': correlation_id,
        'event': event
    })
    survey_id = body_dict['survey_id']
    response_id = body_dict['response_id']
    question_ids = body_dict.get('question_ids')
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
    survey_response = SurveyResponse(response_dict=body_dict, correlation_id=correlation_id)
    survey_response.check_project_task_exists()
    ddb_response = survey_response.put_item()
    return {
        "statusCode": ddb_response['ResponseMetadata']['HTTPStatusCode']
    }
