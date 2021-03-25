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
import local.dev_config  # set env variables
import local.secrets  # set env variables
import os
import src.common.constants as const
import tests.test_data as td
from thiscovery_lib.dynamodb_utilities import Dynamodb
from uuid import uuid4


class DdbMixin:
    @classmethod
    def clear_task_responses_table(cls):
        try:
            cls.ddb_client
        except AttributeError:
            cls.ddb_client = Dynamodb(stack_name=const.STACK_NAME)
        finally:
            cls.ddb_client.delete_all(
                table_name=const.TASK_RESPONSES_TABLE["name"],
                key_name=const.TASK_RESPONSES_TABLE["partition_key"],
                sort_key_name=const.TASK_RESPONSES_TABLE["sort_key"],
            )

    @classmethod
    def clear_personal_links_table(cls):
        try:
            cls.ddb_client
        except AttributeError:
            cls.ddb_client = Dynamodb(stack_name=const.STACK_NAME)
        finally:
            cls.ddb_client.delete_all(
                table_name=const.PersonalLinksTable.NAME,
                key_name=const.PersonalLinksTable.PARTITION,
                sort_key_name=const.PersonalLinksTable.SORT,
            )

    @classmethod
    def add_unassigned_links_to_personal_links_table(cls, n: int) -> None:
        try:
            cls.ddb_client
        except AttributeError:
            cls.ddb_client = Dynamodb(stack_name=const.STACK_NAME)
        finally:
            cls.ddb_client.batch_put_items(
                table_name=const.PersonalLinksTable.NAME,
                items=[
                    {
                        **td.TEST_UNASSIGNED_PERSONAL_LINK_DDB_ITEM,
                        "url": f"https://www.thiscovery.org?random_id={str(uuid4())}",
                    }
                    for _ in range(abs(n))
                ],
                partition_key_name=const.PersonalLinksTable.PARTITION,
            )
