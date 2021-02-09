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


class DdbBaseItem:
    """
    Base class representing a Ddb item
    """
    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if (k[0] != "_") and (k not in ['created', 'modified'])}


class InterviewTask:
    """
    Represents an interview system task
    """
    def __init__(self, interview_task_id, **kwargs):
        self._id = interview_task_id
        optional_attributes = [
            'project_task_id',
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

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if (k[0] != "_") and (k not in ['created', 'modified'])}

    def from_dict(self, interview_task_dict):
        self.__dict__.update(interview_task_dict)

    def ddb_dump(self, update_allowed=False):
        return self._ddb_client.put_item(
            table_name=const.INTERVIEW_TASKS_TABLE,
            key=str(self._id),
            item_type='interview_task',
            item_details=None,
            item=self.as_dict(),
            update_allowed=update_allowed
        )

    def ddb_load(self):
        if self.modified is None:
            item = self._ddb_client.get_item(
                table_name=const.INTERVIEW_TASKS_TABLE,
                key=str(self._id),
            )
            try:
                self.__dict__.update(item)
            except TypeError:
                raise utils.ObjectDoesNotExistError(
                    f'InterviewTask {self._id} could not be found in Dynamodb',
                    details={
                        'InterviewTask': self.as_dict(),
                    }
                )


class UserInterviewTask:
    """
    Represents an interview system user task
    """
    def __init__(self, project_task_id, user_interview_task_id, **kwargs):
        self._project_task_id = project_task_id
        self._id = user_interview_task_id
        optional_attributes = [
            'interview_task_id',
            'anon_project_specific_user_id',
            'anon_user_task_id',
            'modified',
        ]
