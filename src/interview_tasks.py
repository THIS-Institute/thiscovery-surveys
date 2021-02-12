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
import traceback
import uuid
import thiscovery_lib.utilities as utils
from dateutil import parser
from http import HTTPStatus
from thiscovery_lib.core_api_utilities import CoreApiClient
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.qualtrics import qualtrics2thiscovery_timestamp

import common.constants as const
from common.ddb_base_item import DdbBaseItem
from common.task_responses import TaskResponse


class InterviewTask(DdbBaseItem):
    """
    Represents an interview system task item in ddb table InterviewTasks
    """
    def __init__(self, project_task_id, interview_task_id, **kwargs):
        self._project_task_id = project_task_id
        self._interview_task_id = interview_task_id
        optional_attributes = [
            'name',
            'short_name',
            'description',
            'completion_url',
            'on_demand_available',
            'on_demand_survey_id',
            'live_available',
            'live_survey_id',
            'appointment_type_id',
            'modified',
        ]
        for oa in optional_attributes:
            self.__dict__[oa] = kwargs.get(oa)
        self._ddb_client = Dynamodb(stack_name=const.STACK_NAME)

    def ddb_dump(self, update_allowed=False):
        return self._ddb_client.put_item(
            table_name=const.INTERVIEW_TASKS_TABLE,
            key=str(self._project_task_id),
            item_type='interview_task',
            item_details=None,
            item=self.as_dict(),
            update_allowed=update_allowed,
            key_name='project_task_id',
            sort_key={
                'interview_task_id': self._interview_task_id
            }
        )

    def ddb_load(self):
        if self.modified is None:
            item = self._ddb_client.get_item(
                table_name=const.INTERVIEW_TASKS_TABLE,
                key=str(self._project_task_id),
                key_name='project_task_id',
                sort_key={
                    'interview_task_id': self._interview_task_id
                }
            )
            try:
                self.__dict__.update(item)
            except TypeError:
                raise utils.ObjectDoesNotExistError(
                    f'InterviewTask could not be found in Dynamodb',
                    details={
                        'project_task_id': self._project_task_id,
                        'interview_task_id': self._interview_task_id,
                        'InterviewTask': self.as_dict(),
                    }
                )


class UserInterviewTask(TaskResponse):
    """
    Represents an interview system user task item in the TaskResponse Ddb table
    """

    def __init__(self, response_id, event_time=None, anon_project_specific_user_id=None, anon_user_task_id=None,
                 detail=None, correlation_id=None, interview_task_id=None):
        super().__init__(response_id, event_time, anon_project_specific_user_id, anon_user_task_id, detail, correlation_id)
        try:
            self._detail['event_type'] = 'user_interview_task'
        except TypeError:
            self._detail = {'event_type': 'user_interview_task'}
        self.interview_task_id = interview_task_id
        self._core_client = CoreApiClient(correlation_id=correlation_id)
        self.project_task_id = None
        self.interview_task = None

    @classmethod
    def from_eb_event(cls, event):
        detail_type = event['detail-type']
        assert detail_type == 'user_interview_task', f'Unexpected detail-type: {detail_type}'
        task_response = super().from_eb_event(event=event)
        try:
            interview_task_id = task_response._detail.pop('interview_task_id')
        except KeyError:
            raise utils.DetailedValueError(
                'Mandatory interview_task_id data not found in user_interview_task event',
                details={
                    'event': event,
                }
            )
        return cls(
            response_id=task_response._response_id,
            event_time=task_response._event_time,
            anon_project_specific_user_id=task_response.anon_project_specific_user_id,
            anon_user_task_id=task_response.anon_user_task_id,
            detail=task_response._detail,
            correlation_id=task_response._correlation_id,
            interview_task_id=interview_task_id,
        )

    def get_project_task_id(self):
        user_task = self._core_client.get_user_task_from_anon_user_task_id(anon_user_task_id=self.anon_user_task_id)
        self.project_task_id = user_task['project_task_id']

    def get_interview_task(self):
        if self.project_task_id is None:
            self.get_project_task_id()
        interview_task = InterviewTask(
            self.project_task_id,
            self.interview_task_id,
        )
        interview_task.ddb_load()
        self.interview_task = interview_task.as_dict()

    def query_ddb_by_response_id_alone(self):
        user_interview_task_events = self._ddb_client.query(
            table_name=const.TASK_RESPONSES_TABLE,
            filter_attr_name='type',
            filter_attr_values=['user_interview_task'],
            KeyConditionExpression='response_id = :response_id',
            ExpressionAttributeValues={
                ':response_id': self._response_id,
            },
        )
        events_n = len(user_interview_task_events)
        assert events_n == 1, f'Found {events_n} user_interview_tasks in {const.TASK_RESPONSES_TABLE} ddb table; expected 1'
        try:
            return user_interview_task_events[0]
        except (IndexError, AttributeError):
            raise utils.ObjectDoesNotExistError(
                f'user_interview_task could not be found in Dynamodb',
                details={
                    'user_interview_task': self.as_dict(),
                }
            )

    def ddb_load(self):
        self.__dict__.update(self.query_ddb_by_response_id_alone())
