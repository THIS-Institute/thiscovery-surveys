import json
from http import HTTPStatus

import common.utilities as utils
from common.qualtrics import ResponsesClient, SurveyDefinitionsClient


class SurveyClient:
    def __init__(self, survey_id, correlation_id=None):
        self.survey_id = survey_id
        self.correlation_id = correlation_id
        self.responses_client = ResponsesClient(survey_id=survey_id, correlation_id=correlation_id)
        self.survey_definition_client = SurveyDefinitionsClient(survey_id=survey_id, correlation_id=correlation_id)
        self.survey_definition = None

    def convert_question_id_to_response_values_key(self, question_id):
        if not self.survey_definition:
            self.get_survey_definition()
        q_type = self.survey_definition['result']['Questions'][question_id]['QuestionType']
        if q_type == 'MC':
            response_values_key = question_id
        elif q_type == 'TE':
            response_values_key = f'{question_id}_TEXT'
        else:
            raise NotImplementedError(f'Handling of Qualtrics question type {q_type} not implemented')
        return response_values_key

    def get_survey_definition(self):
        self.survey_definition = self.survey_definition_client.get_survey()

    def get_response(self, response_id, question_ids=None):
        r = self.responses_client.retrieve_response(response_id=response_id)
        values = r['result']['values']
        if question_ids is None:
            return values
        else:
            selected_values = dict()
            for q_id in question_ids:
                response_values_key = self.convert_question_id_to_response_values_key(q_id)
                selected_values[q_id] = values.get(response_values_key)
            return selected_values


@utils.lambda_wrapper
@utils.api_error_handler
def get_responses_api(event, context):
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
    response_body = survey_client.get_response(response_id=response_id, question_ids=question_ids)
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(response_body),
    }
