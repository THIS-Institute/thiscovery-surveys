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
from thiscovery_lib.dynamodb_utilities import Dynamodb
import common.constants as const


def put_task_response(event, item=None):
    event_id = event['id']  # note that event id will be used as correlation id for subsequent processing
    event_time = event['time']
    event_detail = event['detail']

    if item is None:
        item = dict()
    default_response_fieldnames = [
        'anon_project_specific_user_id',
        'anon_user_task_id',
    ]
    for a in default_response_fieldnames:
        item[a] = event_detail.pop(a)

    response_id = event_detail.pop('response_id')
    ddb_client = Dynamodb(stack_name=const.STACK_NAME, correlation_id=event_id)
    ddb_client.put_item(
        table_name=const.TASK_RESPONSES_TABLE,
        key=response_id,
        item_type=event_detail.get('event_type', 'task_response'),
        item_details=event_detail,
        item=item,
        key_name='response_id',
        sort_key={'event_time': event_time},
    )
