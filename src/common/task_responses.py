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

    def __init__(self, event):
        self._event_detail = event['detail']
        self._response_id = self._event_detail.pop('response_id')  # partition key
        self._event_time = event['time']  # sort key
        self.anon_project_specific_user_id = self._event_detail.pop('anon_project_specific_user_id', None)
        self.anon_user_task_id = self._event_detail.pop('anon_user_task_id', None)
        self._correlation_id = event['id']
        self._ddb_client = Dynamodb(stack_name=const.STACK_NAME, correlation_id=self._correlation_id)

    def ddb_dump(self, update_allowed=False):
        return self._ddb_client.put_item(
            table_name=const.TASK_RESPONSES_TABLE,
            key=self._response_id,
            item_type=self._event_detail.pop('event_type', 'task_response'),
            item_details=self._event_detail,
            item=self.as_dict(),
            update_allowed=update_allowed,
            key_name='response_id',
            sort_key={'event_time': self._event_time},
        )
