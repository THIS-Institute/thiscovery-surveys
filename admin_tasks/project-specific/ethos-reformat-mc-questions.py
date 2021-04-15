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
from __future__ import annotations
import local.dev_config
import local.secrets
import json
import regex
from pprint import pprint
from thiscovery_lib.qualtrics import SurveyDefinitionsClient
from thiscovery_lib.utilities import get_logger
from local.secrets import ETHOS_SURVEY_ID as SURVEY_ID


logger = get_logger()


importance_original_choices = {
    "1": {"Display": "Extremely unimportant"},
    "2": {"Display": "Unimportant"},
    "3": {"Display": "Quite unimportant"},
    "4": {"Display": "Undecided"},
    "5": {"Display": "Quite important"},
    "6": {"Display": "Important"},
    "7": {"Display": "Extremely important"},
}


agreement_original_choices_v1 = {
    "1": {"Display": "Strongly disagree"},
    "2": {"Display": "Disagree"},
    "3": {"Display": "Somewhat disagree"},
    "4": {"Display": "Neither agree nor disagree"},
    "5": {"Display": "Somewhat agree"},
    "6": {"Display": "Agree"},
    "7": {"Display": "Strongly agree"},
}


agreement_original_choices_v2 = {
    **agreement_original_choices_v1,
    "4": {"Display": "Undecided"},
}


agreement_original_choices_v3 = {
    "1": {"Display": "Strongly disagree"},
    "2": {"Display": "Disagree"},
    "3": {"Display": "Somewhat disagree"},
    "5": {"Display": "Somewhat agree"},
    "6": {"Display": "Agree"},
    "7": {"Display": "Strongly agree"},
    "8": {"Display": "Undecided"},
}


importance_target_choices = {
    "1": {"Display": "Extremely important"},
    "2": {"Display": "Important"},
    "3": {"Display": "Somewhat important"},
    "4": {"Display": "Undecided"},
    "5": {"Display": "Somewhat unimportant"},
    "6": {"Display": "Unimportant"},
    "7": {"Display": "Extremely unimportant"},
}


agreement_target_choices = {
    "1": {"Display": "Strongly agree"},
    "2": {"Display": "Agree"},
    "3": {"Display": "Somewhat agree"},
    "4": {"Display": "Undecided"},
    "5": {"Display": "Somewhat disagree"},
    "6": {"Display": "Disagree"},
    "7": {"Display": "Strongly disagree"},
}

choices_mapping = {
    json.dumps(agreement_original_choices_v1): agreement_target_choices,
    json.dumps(agreement_original_choices_v2): agreement_target_choices,
    json.dumps(agreement_original_choices_v3): agreement_target_choices,
    json.dumps(importance_original_choices): importance_target_choices,
}


mc_question_target = {
    "ChoiceOrder": ["1", "2", "3", "4", "5", "6", "7"],
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


def adjust_choices_order(
    questions: dict,
    mapping: dict[str, dict],
    question_target_template: dict,
    number_of_choices: int,
) -> dict:
    choices_to_update = [json.loads(k) for k, _ in mapping.items()]
    updated_questions = dict()
    for k, v in questions.items():
        choice_order_len = len(v.get("ChoiceOrder", list()))
        if (choice_order_len == number_of_choices) and (
            choices := v.get("Choices")
        ) in choices_to_update:
            updated_choices = mapping[json.dumps(choices)]
            updated_v = {
                **v,
                **question_target_template,
                "Choices": updated_choices,
            }
            logger.debug(
                "Question with updated choices",
                extra={"choices": updated_v["Choices"], "tag": v["DataExportTag"]},
            )
            updated_questions[k] = updated_v
    return updated_questions


def main(dry_run=False):
    dry_run_postfix = ""
    if dry_run:
        dry_run_postfix = (
            "(this was a dry run, so no changes were actually made to the survey)"
        )
    survey_client = SurveyDefinitionsClient(survey_id=SURVEY_ID)
    survey = survey_client.get_survey()["result"]
    questions = survey["Questions"]

    # # adjust choice order
    # adjusted_order_questions = adjust_choices_order(
    #     questions=questions,
    #     mapping=choices_mapping,
    #     question_target_template=mc_question_target,
    #     number_of_choices=7,
    # )
    # if not dry_run:
    #     for k, v in adjusted_order_questions.items():
    #         survey_client.update_question(question_id=k, data=v)
    # print(
    #     f"Choice order of {len(adjusted_order_questions)} questions was updated {dry_run_postfix}"
    # )
    # questions.update(adjusted_order_questions)
    # # logger.info("Questions", extra={"questions": questions})

    # replace modal prompt
    modal_link_re = regex.compile(
        '(<p><span class="info-icon">ⓘ</span> <a href="#modal-(\d+)" rel="modal:open">'
        "Read more about this statement</a>.</p>){e<=3}",  # allow up to 3 errors
        regex.ENHANCEMATCH,
    )
    target_link = '<p><span class="info-icon">ⓘ</span> <a href="#modal-{}" rel="modal:open">Read more about this statement</a></p>'
    updated_questions_counter = 0
    updated_questions_tags = list()
    for k, v in questions.items():
        question_text = v["QuestionText"]
        tag = v["DataExportTag"]
        if (m := modal_link_re.search(question_text)) :
            v["QuestionText"] = question_text.replace(
                m.group(1), target_link.format(m.group(2))
            )
            logger.debug(
                "Question text after replacement",
                extra={"question text": v["QuestionText"]},
            )
            updated_questions_counter += 1
            updated_questions_tags.append(tag)
            if not dry_run:
                survey_client.update_question(question_id=k, data=v)
    print(
        f"Modal prompt updated in {updated_questions_counter} questions {dry_run_postfix}"
    )
    # print(f"Here are their tags: {updated_questions_tags}")


if __name__ == "__main__":
    main(dry_run=False)
