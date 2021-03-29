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
import local.dev_config
import local.secrets
from copy import deepcopy
from pprint import pprint
from thiscovery_lib.qualtrics import SurveyDefinitionsClient
from local.secrets import ETHOS_SURVEY_ID as SURVEY_ID


original_choices = {
    "1": {"Display": "1"},
    "2": {"Display": "2"},
    "3": {"Display": "3"},
    "4": {"Display": "4"},
    "5": {"Display": "5"},
    "6": {"Display": "6"},
    "7": {"Display": "7"},
}


mc_question_target = {
    "ChoiceOrder": ["1", "2", "3", "4", "5", "6", "7"],
    "Choices": {
        "1": {"Display": "Strongly disagree"},
        "2": {"Display": "Disagree"},
        "3": {"Display": "Somewhat disagree"},
        "4": {"Display": "Neither agree nor disagree"},
        "5": {"Display": "Somewhat agree"},
        "6": {"Display": "Agree"},
        "7": {"Display": "Strongly agree"},
    },
    "Configuration": {
        "LabelPosition": "SIDE",
        "QuestionDescriptionOption": "UseText",
    },
    "DataVisibility": {"Hidden": False, "Private": False},
    "Language": [],
    "NextAnswerId": 1,
    "NextChoiceId": 8,
    "QuestionJS": False,
    "QuestionType": "MC",
    "Selector": "SAVR",
    "SubSelector": "TX",
    "Validation": {
        "Settings": {
            "ForceResponse": "OFF",
            "ForceResponseType": "ON",
            "Type": "None",
        }
    },
}


def main():
    survey_client = SurveyDefinitionsClient(survey_id=SURVEY_ID)
    survey = survey_client.get_survey()["result"]
    questions = survey["Questions"]
    for k, v in questions.items():
        updated_question = None
        if v.get("Choices") == original_choices:
            v.update(mc_question_target)
            updated_question = True
        else:
            print(f"Skipped question: {k}")

        if updated_question:
            survey_client.update_question(question_id=k, data=v)


if __name__ == "__main__":
    main()
