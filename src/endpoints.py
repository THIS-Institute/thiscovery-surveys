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
from thiscovery_lib.events_api_utilities import EventsApiClient

from common.survey_response import SurveyClient, SurveyResponse
from common.survey_definition import SurveyDefinition
from common.task_responses import TaskResponse
from consent import ConsentEvent
from interview_tasks import InterviewTask, UserInterviewTask


@utils.lambda_wrapper
@utils.api_error_handler
def retrieve_responses_api(event, context):
    logger = event["logger"]
    correlation_id = event["correlation_id"]
    parameters = event["queryStringParameters"]
    logger.info(
        "API call",
        extra={
            "parameters": parameters,
            "correlation_id": correlation_id,
        },
    )
    survey_id = parameters.get("survey_id")
    response_id = parameters.get("response_id")
    question_ids = parameters.get("question_ids")
    if question_ids:
        question_ids = json.loads(question_ids)
    survey_client = SurveyClient(survey_id=survey_id, correlation_id=correlation_id)
    response_body = survey_client.get_response(
        response_id=response_id, export_tags=question_ids
    )
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(response_body),
    }


@utils.lambda_wrapper
@utils.api_error_handler
def put_response_api(event, context):
    logger = event["logger"]
    correlation_id = event["correlation_id"]
    body_dict = json.loads(event["body"])
    logger.info(
        "API call",
        extra={
            "body_dict": body_dict,
            "correlation_id": correlation_id,
            "event": event,
        },
    )
    alarm_test = body_dict.get("brew_coffee")
    if alarm_test:
        raise utils.DeliberateError("Coffee is not available", details={})
    survey_response = SurveyResponse(
        response_dict=body_dict, correlation_id=correlation_id
    )
    survey_response.check_project_task_exists()
    ddb_response = survey_response.put_item()
    logger.debug(
        "Dynamodb response",
        extra={
            "ddb_response": ddb_response,
            "correlation_id": correlation_id,
        },
    )
    return {"statusCode": HTTPStatus.NO_CONTENT}


@utils.lambda_wrapper
@utils.api_error_handler
def send_consent_email_api(event, context):
    consent_event = ConsentEvent(survey_consent_event=event)
    dump_result, notification_result = consent_event.parse()
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(
            {
                "store_result": dump_result,
                "notification_result": notification_result,
            }
        ),
    }


@utils.lambda_wrapper
def put_task_response(event, context):
    pass


@utils.lambda_wrapper
def put_interview_questions(event, context):
    """
    Handles interview_questions_update events posted by Qualtrics
    """
    try:
        event_for_interview_system = {
            "detail-type": event["detail-type"],
            "detail": {
                "survey_id": event["detail"]["survey_id"],
            },
        }
    except KeyError as err:
        raise utils.DetailedValueError(
            f"interview_questions_update event missing mandatory data {err}", details={}
        )
    sd = SurveyDefinition.from_eb_event(event=event)
    body = sd.ddb_update_interview_questions()
    eac = EventsApiClient()
    eac.post_event(event_for_interview_system)
    return {"statusCode": HTTPStatus.OK, "body": json.dumps(body)}


@utils.lambda_wrapper
def put_user_agent_data(event, context):
    """
    Handles survey_user_agent events posted by Qualtrics
    """
    uad = TaskResponse.from_eb_event(event=event)
    uad.get_project_task_id()
    uad.ddb_dump(unpack_detail=True)
    return {"statusCode": HTTPStatus.OK, "body": ""}


@utils.lambda_wrapper
def put_user_interview_task(event, context):
    """
    Handles create-user-interview-task events posted by Qualtrics
    """
    uit = UserInterviewTask.from_eb_event(event=event)
    uit.get_interview_task()
    uit.ddb_dump()
    return {"statusCode": HTTPStatus.OK, "body": json.dumps(uit.as_dict())}


@utils.lambda_wrapper
@utils.api_error_handler
def get_user_interview_task_api(event, context):
    """
    Responds to get-user-interview-task requests coming from the interview system
    """
    logger = event["logger"]
    correlation_id = event["correlation_id"]
    response_id = event["pathParameters"]["id"]
    logger.info(
        "API call",
        extra={
            "response_id": response_id,
            "correlation_id": correlation_id,
            "event": event,
        },
    )
    uit = UserInterviewTask(response_id=response_id)
    uit.ddb_load()
    body = uit.as_dict()
    for a in ["details", "type"]:
        del body[a]
        del body["interview_task"][a]
    del body["project_task_id"]
    return {"statusCode": HTTPStatus.OK, "body": json.dumps(body)}


@utils.lambda_wrapper
@utils.api_error_handler
def get_interview_task_api(event, context):
    """
    Responds to get-interview-task requests coming from the interview system
    """
    logger = event["logger"]
    correlation_id = event["correlation_id"]
    interview_task_id = event["pathParameters"]["id"]
    logger.info(
        "API call",
        extra={
            "interview_task_id": interview_task_id,
            "correlation_id": correlation_id,
            "event": event,
        },
    )
    it = InterviewTask(interview_task_id=interview_task_id)
    it.ddb_load()
    body = it.as_dict()
    for a in ["details", "type"]:
        del body[a]
    return {"statusCode": HTTPStatus.OK, "body": json.dumps(body)}


@utils.lambda_wrapper
@utils.api_error_handler
def get_interview_questions_api(event, context):
    logger = event["logger"]
    correlation_id = event["correlation_id"]
    survey_id = event["pathParameters"]["id"]
    logger.info(
        "API call",
        extra={
            "survey_id": survey_id,
            "correlation_id": correlation_id,
            "event": event,
        },
    )
    body = SurveyDefinition.get_interview_questions(survey_id)

    return {"statusCode": HTTPStatus.OK, "body": json.dumps(body)}
