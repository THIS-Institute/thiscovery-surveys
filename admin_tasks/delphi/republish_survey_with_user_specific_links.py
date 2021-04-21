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
"""
This script generates individual distribution links for a pre-existing survey and contact list (aka mailing list) in Qualtrics,
and exports those links to Dynamodb

Usage: Run this file after setting the values of account, survey_id, and contact_list_id
"""
import local.dev_config  # sets env variables TEST_ON_AWS and AWS_TEST_API
import local.secrets  # sets env variables THISCOVERY_AFS25_PROFILE and THISCOVERY_AMP205_PROFILE
from src.personal_links import DistributionLinksGenerator


def main(account, survey_id, contact_list_id):
    link_generator = DistributionLinksGenerator(
        account=account, survey_id=survey_id, contact_list_id=contact_list_id
    )
    link_generator.generate_links_and_upload_to_dynamodb()
    # ut.clear_user_tasks_for_project_task_id(PROJECT_TASK_ID)  # todo: this is thiscovery-core code. Move to dev-tools?


if __name__ == "__main__":
    main(
        account="cambridge",
        survey_id=None,
        contact_list_id=None,
    )
