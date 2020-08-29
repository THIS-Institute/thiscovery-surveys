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
import datetime
import requests
import thiscovery_lib.utilities as utils


class BaseClient:

    def __init__(self, api_token=None, correlation_id=None):
        self.base_url = 'https://cambridge.eu.qualtrics.com/API'
        if api_token is None:
            self.api_token = utils.get_secret('qualtrics-connection')['api-key']
        else:
            self.api_token = api_token
        self.logger = utils.get_logger()
        self.correlation_id = correlation_id

    def qualtrics_request(self, method, endpoint_url, api_key=None, params=None, data=None):
        if api_key is None:
            api_key = self.api_token

        headers = {
            "content-type": "application/json",
            "Accept": "application/json",
            "x-api-token": api_key,
        }

        self.logger.debug('Qualtrics API call', extra={'method': method, 'url': endpoint_url, 'params': params, 'json': data})
        response = requests.request(
            method=method,
            url=endpoint_url,
            params=params,
            headers=headers,
            json=data,
        )

        if response.ok:
            return response.json()
        else:
            print(response.text)
            raise utils.DetailedValueError('Call to Qualtrics API failed', details={'response.text': response.text})


class SurveyDefinitionsClient(BaseClient):

    def __init__(self, survey_id=None, correlation_id=None):
        super().__init__(correlation_id=correlation_id)
        self.base_endpoint = f"{self.base_url}/v3/survey-definitions"
        self.survey_endpoint = f"{self.base_endpoint}/{survey_id}"
        self.questions_endpoint = f"{self.survey_endpoint}/questions"
        self.blocks_endpoint = f"{self.survey_endpoint}/blocks"

    def refresh_survey_endpoints(self, survey_id):
        self.survey_endpoint = f"{self.base_endpoint}/{survey_id}"
        self.questions_endpoint = f"{self.survey_endpoint}/questions"
        self.blocks_endpoint = f"{self.survey_endpoint}/blocks"

    def get_survey(self):
        return self.qualtrics_request("GET", self.survey_endpoint)

    def create_survey(self, survey_name):
        data = {
            "SurveyName": survey_name,
            "Language": "EN-GB",
            "ProjectCategory": "CORE"
        }
        response = self.qualtrics_request("POST", self.base_endpoint, data=data)
        if response["meta"]["httpStatus"] == "200 - OK":
            survey_id = response["result"]["SurveyID"]
            self.refresh_survey_endpoints(survey_id)
            return survey_id
        else:
            raise utils.DetailedValueError("API call to Qualtrics create survey method failed", details={'response': response})

    def create_question(self, data):
        return self.qualtrics_request("POST", self.questions_endpoint, data=data)

    def update_question(self, question_id, data):
        endpoint = f"{self.questions_endpoint}/{question_id}"
        return self.qualtrics_request("PUT", endpoint, data=data)

    def delete_question(self, question_id):
        endpoint = f"{self.questions_endpoint}/{question_id}"
        return self.qualtrics_request("DELETE", endpoint)
    
    def create_block(self, data):
        return self.qualtrics_request("POST", self.blocks_endpoint, data=data)

    def update_block(self, block_id, data):
        endpoint = f"{self.blocks_endpoint}/{block_id}"
        return self.qualtrics_request("PUT", endpoint, data=data)

    def delete_block(self, block_id):
        endpoint = f"{self.blocks_endpoint}/{block_id}"
        return self.qualtrics_request("DELETE", endpoint)


class DistributionsClient(BaseClient):
    def __init__(self, correlation_id=None):
        super().__init__(correlation_id=correlation_id)
        self.base_endpoint = f"{self.base_url}/v3/distributions"

    def _create_distribution(self, data):
        """
        https://api.qualtrics.com/api-reference/reference/distributions.json/paths/~1distributions/post
        """
        return self.qualtrics_request("POST", self.base_endpoint, data=data)

    def create_individual_links(self, survey_id, contact_list_id, **kwargs):
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d_%H:%M:%S")
        expiration = now + datetime.timedelta(days=90)
        expiration_str = expiration.strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "surveyId": survey_id,
            "linkType": "Individual",
            "description": f"distribution_{survey_id}_{now_str}",
            "action": "CreateDistribution",
            "expirationDate": expiration_str,
            "mailingListId": contact_list_id,
        }
        data.update(**kwargs)
        return self._create_distribution(data=data)

    def list_distribution_links(self, distribution_id, survey_id):
        """
        https://api.qualtrics.com/api-reference/reference/distributions.json/paths/~1distributions~1%7BdistributionId%7D~1links/get
        """
        endpoint = f'{self.base_endpoint}/{distribution_id}/links'
        params = {
            'surveyId': survey_id,
        }
        return self.qualtrics_request("GET", endpoint, params=params)

    def delete_distribution(self, distribution_id):
        """
        https://api.qualtrics.com/api-reference/reference/distributions.json/paths/~1distributions~1%7BdistributionId%7D/delete
        """
        endpoint = f'{self.base_endpoint}/{distribution_id}'
        return self.qualtrics_request("DELETE", endpoint)


class ResponsesClient(BaseClient):
    def __init__(self, survey_id, correlation_id=None):
        super().__init__(correlation_id=correlation_id)
        self.base_endpoint = f"{self.base_url}/v3/surveys/{survey_id}"

    def retrieve_survey_response_schema(self):
        """
        https://api.qualtrics.com/api-reference/reference/singleResponses.json/paths/~1surveys~1%7BsurveyId%7D~1response-schema/get
        """
        url = f"{self.base_endpoint}/response-schema"
        response = self.qualtrics_request("GET", endpoint_url=url)
        assert response['meta']['httpStatus'] == '200 - OK', f'Qualtrics API call failed with response: {response}'
        return response

    def retrieve_response(self, response_id):
        """
        https://api.qualtrics.com/api-reference/reference/singleResponses.json/paths/~1surveys~1%7BsurveyId%7D~1responses~1%7BresponseId%7D/get
        """
        url = f"{self.base_endpoint}/responses/{response_id}"
        response = self.qualtrics_request("GET", endpoint_url=url)
        assert response['meta']['httpStatus'] == '200 - OK', f'Qualtrics API call failed with response: {response}'
        return response
