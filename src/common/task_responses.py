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
import thiscovery_lib.utilities as utils
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.core_api_utilities import CoreApiClient

import common.constants as const
from common.ddb_base_item import DdbBaseItem


class TaskResponse(DdbBaseItem):
    """
    Base class representing a TaskResponse Ddb item
    """

    def __init__(self, response_id, event_time, anon_project_specific_user_id=None, anon_user_task_id=None,
                 detail_type=None, detail=None, correlation_id=None):
        self._response_id = response_id
        self._event_time = event_time
        self.anon_project_specific_user_id = anon_project_specific_user_id
        self.anon_user_task_id = anon_user_task_id
        self._detail_type = detail_type
        self._detail = detail
        self._correlation_id = correlation_id
        self._core_client = CoreApiClient(correlation_id=correlation_id)
        self._ddb_client = Dynamodb(stack_name=const.STACK_NAME, correlation_id=correlation_id)
        self.project_task_id = None

    @classmethod
    def from_eb_event(cls, event):
        event_detail = event['detail']
        response_id = event_detail.pop('response_id')
        event_time = event['time']
        try:
            anon_project_specific_user_id = event_detail.pop('anon_project_specific_user_id')
            anon_user_task_id = event_detail.pop('anon_user_task_id')
        except KeyError as exc:
            raise utils.DetailedValueError(
                f'Mandatory {exc} data not found in source event',
                details={
                    'event': event,
                }
            )
        return cls(
            response_id=response_id,
            event_time=event_time,
            anon_project_specific_user_id=anon_project_specific_user_id,
            anon_user_task_id=anon_user_task_id,
            detail_type=event['detail-type'],
            detail=event_detail,
            correlation_id=event['id']
        )

    def get_project_task_id(self):
        user_task = self._core_client.get_user_task_from_anon_user_task_id(anon_user_task_id=self.anon_user_task_id)
        self.project_task_id = user_task['project_task_id']

    def ddb_dump(self, update_allowed=False, unpack_detail=False):
        item = self.as_dict()
        if unpack_detail:
            item.update(self._detail)
            self._detail = dict()
        return self._ddb_client.put_item(
            table_name=const.TASK_RESPONSES_TABLE['name'],
            key=self._response_id,
            item_type=self._detail_type,
            item_details=self._detail,
            item=item,
            update_allowed=update_allowed,
            key_name=const.TASK_RESPONSES_TABLE['partition_key'],
            sort_key={const.TASK_RESPONSES_TABLE['sort_key']: self._event_time},
        )
