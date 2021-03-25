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
import local.dev_config  # sets env variables TEST_ON_AWS and AWS_TEST_API
import local.secrets  # sets env variables THISCOVERY_AFS25_PROFILE and THISCOVERY_AMP205_PROFILE
import copy
import json
import thiscovery_dev_tools.testing_tools as test_utils
import thiscovery_lib.utilities as utils
from http import HTTPStatus
from uuid import uuid4
from pprint import pprint
from thiscovery_lib.dynamodb_utilities import Dynamodb

import src.personal_links as pl
import src.common.constants as const
import tests.test_data as td
from tests.testing_utilities import DdbMixin


class TestPersonalLinkApi(test_utils.BaseTestCase, DdbMixin):
    entity_base_url = "v1/personal-link"
    default_survey_id = td.QUALTRICS_TEST_OBJECTS["unittest-survey-1"]["id"]
    default_user_id = "8518c7ed-1df4-45e9-8dc4-d49b57ae0663"  # Clive
    default_account = "cambridge"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clear_personal_links_table()

    def routine_01(self, expected_base_url: str) -> tuple:
        account = self.default_account
        survey_id = self.default_survey_id
        user_id = self.default_user_id
        params = {
            "survey_id": survey_id,
            "user_id": user_id,
            "account": account,
        }
        expected_status = HTTPStatus.OK
        result = test_utils.test_get(
            pl.get_personal_link_api,
            self.entity_base_url,
            querystring_parameters=params,
        )
        self.assertEqual(expected_status, result["statusCode"])

        # check personal link is what we expect
        result_body = json.loads(result["body"])
        personal_link = result_body["personal_link"]
        self.assertEqual(
            expected_base_url,
            personal_link.split("?")[0],
        )

        # check ddb item has been assigned
        item = self.ddb_client.get_item(
            table_name=const.PersonalLinksTable.NAME,
            key=f"{account}_{survey_id}",
            key_name=const.PersonalLinksTable.PARTITION,
            sort_key={const.PersonalLinksTable.SORT: personal_link},
        )
        self.assertEqual("assigned", item["status"])
        self.assertEqual(user_id, item["user_id"])
        return account, user_id, personal_link, result

    def test_get_personal_link_api_ok_assigned_link_exists(self):
        table = self.ddb_client.get_table(table_name=const.PersonalLinksTable.NAME)
        table.put_item(Item=td.TEST_ASSIGNED_PERSONAL_LINK_DDB_ITEM)
        self.routine_01(
            "https://cambridge.eu.qualtrics.com//jfe/form/SV_2avH1JdVZa8eEAd"
        )

    def test_get_personal_link_api_ok_unassigned_links_exist_buffer_ok(self):
        self.clear_personal_links_table()
        self.add_unassigned_links_to_personal_links_table(
            const.PersonalLinksTable.BUFFER
        )
        self.routine_01("https://www.thiscovery.org")

    def test_get_personal_link_api_ok_unassigned_links_exist_buffer_low(self):
        self.clear_personal_links_table()
        self.add_unassigned_links_to_personal_links_table(
            const.PersonalLinksTable.BUFFER - 1
        )
        self.routine_01("https://www.thiscovery.org")

    def test_get_personal_link_api_ok_empty_table(self):
        self.clear_personal_links_table()
        account, user_id, personal_link, result = self.routine_01(
            "https://cambridge.eu.qualtrics.com//jfe/form/SV_2avH1JdVZa8eEAd"
        )

        # check we have the expected number of links in ddb table
        links = self.ddb_client.scan(table_name=const.PersonalLinksTable.NAME)
        self.assertEqual(const.DISTRIBUTION_LISTS[account]["length"], len(links))

        # check personal link status has been updated to assigned and given an user_id
        for link in links:
            status = link["status"]
            keys = link.keys()
            if link["url"] == personal_link:
                self.assertEqual("assigned", status)
                self.assertEqual(user_id, link["user_id"])
            else:
                self.assertEqual("new", status)
                self.assertNotIn("user_id", keys)

    def test_get_personal_link_api_invalid_account(self):
        invalid_account = "oxford"
        params = {
            "survey_id": self.default_survey_id,
            "user_id": self.default_user_id,
            "account": invalid_account,
        }
        expected_status = HTTPStatus.BAD_REQUEST
        result = test_utils.test_get(
            pl.get_personal_link_api,
            self.entity_base_url,
            querystring_parameters=params,
        )
        self.assertEqual(expected_status, result["statusCode"])

    def test_get_personal_link_api_missing_mandatory_data(self):
        params = {
            "survey_id": self.default_survey_id,
            "account": self.default_account,
        }
        expected_status = HTTPStatus.BAD_REQUEST
        result = test_utils.test_get(
            pl.get_personal_link_api,
            self.entity_base_url,
            querystring_parameters=params,
        )
        self.assertEqual(expected_status, result["statusCode"])
