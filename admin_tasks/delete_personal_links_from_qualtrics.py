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
from pprint import pprint
from tests.test_data import QUALTRICS_TEST_OBJECTS
from thiscovery_lib.qualtrics import DistributionsClient


def main(survey_to_clear):
    dc = DistributionsClient()
    distributions = dc.list_distributions(survey_id=survey_to_clear)
    for dist in distributions:
        dc.delete_distribution(distribution_id=dist["id"])


if __name__ == "__main__":
    main(survey_to_clear=QUALTRICS_TEST_OBJECTS["unittest-survey-1"]["id"])
