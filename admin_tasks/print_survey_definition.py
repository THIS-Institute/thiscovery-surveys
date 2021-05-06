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
from thiscovery_lib.qualtrics import SurveyDefinitionsClient
from local.secrets import OFIG_SURVEY_ID as SURVEY_ID


survey_client = SurveyDefinitionsClient(survey_id=SURVEY_ID)
survey = survey_client.get_survey()["result"]
with open("survey_definition.py", "w") as sd:
    pprint(survey, sd)

# # iterate through questions
# questions = survey["Questions"]
# questions_to_update_counter = 0
# tags_to_update = list()
# for k, v in questions.items():
#     tag = v["DataExportTag"]
#     question_text = v["QuestionText"]
#     if "click here" in question_text:
#         print(tag, k, question_text)
#         # choice_order_len = len(v.get("ChoiceOrder", list()))
#         # print(tag, k, choice_order_len)
#         # if choice_order_len == 7:
#         #     choices = v["Choices"]
#         #     if (ck := list(choices.keys())) != ["1", "2", "3", "4", "5", "6", "7"]:
#         #         print(f"WARNING: Choices ({ck}) need re-coding!")
#         #         pprint(v)
#         questions_to_update_counter += 1
#         tags_to_update.append(tag)
#     #     # print(v["DataExportTag"])
#     #     pprint([x["Display"] for x in choices.values()])
#     print("\n")
# print(
#     f"{questions_to_update_counter} MC questions with 7 choices were found in survey {SURVEY_ID}"
# )
# print(f"Here are their tags: {tags_to_update}")
