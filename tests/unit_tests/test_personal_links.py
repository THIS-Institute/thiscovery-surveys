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
import json
import thiscovery_dev_tools.testing_tools as test_utils
from http import HTTPStatus
from pprint import pprint

import src.personal_links as pl
import src.common.constants as const
import tests.test_data as td
from thiscovery_dev_tools.test_data.survey_personal_links import (
    TEST_ASSIGNED_PERSONAL_LINK_DDB_ITEM,
    TEST_UNASSIGNED_PERSONAL_LINK_DDB_ITEM,
    TEST_CREATE_PERSONAL_LINKS_EB_EVENT,
)
from tests.testing_utilities import DdbMixin


class TestPersonalLinksBaseClass(test_utils.BaseTestCase, DdbMixin):
    entity_base_url = "v1/personal-link"
    default_survey_id = td.QUALTRICS_TEST_OBJECTS["unittest-survey-1"]["id"]
    default_anon_project_specific_user_id = (
        "87b8f9a8-2400-4259-a8d9-a2f0b16d9ea1"  # Clive
    )
    default_account = "cambridge"

    def check_number_of_links_in_ddb_matches_distribution_list(
        self, additional_links=0
    ):
        links = self.ddb_client.scan(table_name=const.PersonalLinksTable.NAME)
        self.assertEqual(
            (
                const.DISTRIBUTION_LISTS[self.default_account]["length"]
                + additional_links
            ),
            len(links),
        )
        return links


class TestPersonalLinkManager(TestPersonalLinksBaseClass):
    def test_assign_link_to_user_recursion_ok(self):
        self.clear_personal_links_table()
        table = self.ddb_client.get_table(table_name=const.PersonalLinksTable.NAME)
        table.put_item(Item=TEST_ASSIGNED_PERSONAL_LINK_DDB_ITEM)
        account, survey_id = TEST_ASSIGNED_PERSONAL_LINK_DDB_ITEM[
            "account_survey_id"
        ].split("_", maxsplit=1)
        anon_project_specific_user_id = "e132c198-06d3-4200-a6c0-cc3bc7991828"  # Delia
        plm = pl.PersonalLinkManager(
            survey_id=survey_id,
            anon_project_specific_user_id=anon_project_specific_user_id,
            account=account,
        )
        user_link = plm._assign_link_to_user([TEST_UNASSIGNED_PERSONAL_LINK_DDB_ITEM])
        previously_assigned_link = TEST_ASSIGNED_PERSONAL_LINK_DDB_ITEM["url"]

        # user_link_should be a freshly created link with same base url as previously_assigned_link
        self.assertNotEqual(previously_assigned_link, user_link)
        self.assertEqual(
            previously_assigned_link.split("?")[0], user_link.split("?")[0]
        )

        # ddb table should contain previously assigned link + newly created links
        links = self.check_number_of_links_in_ddb_matches_distribution_list(
            additional_links=1
        )

        # two links should be assigned
        assigned_link_users = [
            x["anon_project_specific_user_id"]
            for x in links
            if x["status"] == "assigned"
        ]
        expected_users = [
            anon_project_specific_user_id,
            TEST_ASSIGNED_PERSONAL_LINK_DDB_ITEM["anon_project_specific_user_id"],
        ]
        self.assertCountEqual(expected_users, assigned_link_users)


class TestCreatePersonalLinksEventHandler(TestPersonalLinksBaseClass):
    def test_create_personal_links_ok(self):
        self.clear_personal_links_table()
        pl.create_personal_links(TEST_CREATE_PERSONAL_LINKS_EB_EVENT, None)
        self.check_number_of_links_in_ddb_matches_distribution_list()


class TestPersonalLinkApi(TestPersonalLinksBaseClass):
    def default_call_and_assertions(self, expected_base_url: str) -> tuple:
        account = self.default_account
        survey_id = self.default_survey_id
        anon_project_specific_user_id = self.default_anon_project_specific_user_id
        params = {
            "survey_id": survey_id,
            "anon_project_specific_user_id": anon_project_specific_user_id,
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
        self.assertEqual(
            anon_project_specific_user_id, item["anon_project_specific_user_id"]
        )
        return account, anon_project_specific_user_id, personal_link, result

    def test_get_personal_link_api_ok_assigned_link_exists(self):
        self.get_ddb_client()
        table = self.ddb_client.get_table(table_name=const.PersonalLinksTable.NAME)
        table.put_item(Item=TEST_ASSIGNED_PERSONAL_LINK_DDB_ITEM)
        self.default_call_and_assertions(
            "https://cambridge.eu.qualtrics.com//jfe/form/SV_2avH1JdVZa8eEAd"
        )

    def test_get_personal_link_api_ok_unassigned_links_exist_buffer_ok(self):
        self.clear_personal_links_table()
        self.add_unassigned_links_to_personal_links_table(
            const.PersonalLinksTable.BUFFER
        )
        self.default_call_and_assertions("https://www.thiscovery.org")

    def test_get_personal_link_api_ok_unassigned_links_exist_buffer_low(self):
        self.clear_personal_links_table()
        self.add_unassigned_links_to_personal_links_table(
            const.PersonalLinksTable.BUFFER - 1
        )
        self.default_call_and_assertions("https://www.thiscovery.org")

    def test_get_personal_link_api_ok_empty_table(self):
        self.clear_personal_links_table()
        (
            account,
            anon_project_specific_user_id,
            personal_link,
            result,
        ) = self.default_call_and_assertions(
            "https://cambridge.eu.qualtrics.com//jfe/form/SV_2avH1JdVZa8eEAd"
        )

        # check we have the expected number of links in ddb table
        links = self.check_number_of_links_in_ddb_matches_distribution_list()
        # check personal link status has been updated to assigned and given an anon_project_specific_user_id
        for link in links:
            status = link["status"]
            keys = link.keys()
            if link["url"] == personal_link:
                self.assertEqual("assigned", status)
                self.assertEqual(
                    anon_project_specific_user_id, link["anon_project_specific_user_id"]
                )
            else:
                self.assertEqual("new", status)
                self.assertNotIn("anon_project_specific_user_id", keys)

    def test_get_personal_link_api_invalid_account(self):
        invalid_account = "oxford"
        params = {
            "survey_id": self.default_survey_id,
            "anon_project_specific_user_id": self.default_anon_project_specific_user_id,
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
