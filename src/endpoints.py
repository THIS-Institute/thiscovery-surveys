import json
from http import HTTPStatus

import common.utilities as utils
from common.qualtrics import ResponsesClient


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
    response_body = survey_client.get_response(response_id=response_id, export_tags=question_ids)
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(response_body),
    }
