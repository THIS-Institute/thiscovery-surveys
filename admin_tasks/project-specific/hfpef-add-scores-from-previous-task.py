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
import re

import local.dev_config
import local.secrets
from copy import deepcopy
from pprint import pprint
from thiscovery_lib.qualtrics import SurveyDefinitionsClient
from thiscovery_lib.utilities import get_logger
from local.secrets import HFPEF_SURVEY_ID as SURVEY_ID

t2_to_t1_mapping = {
    "Q3.1": "Q7.4_1",
    "Q4.1": "Q7.4_2",
    "Q5.1": "Q7.4_3",
    "Q6.1": "Q7.4_5",
    "Q7.1": "Q7.4_7",
    "Q8.1": "Q10.1_5",
    "Q9.1": "Q10.1_6",
    "Q11.1": "Q10.1_10",
    "Q12.1": "Q8.3_11",
    "Q13.1": "Q11.1_5",
    "Q14.1": "Q11.1_6",
    "Q15.1": "Q11.1_9",
    "Q16.1": "Q13.1_5",
    "Q17.1": "Q11.1_7",
    "Q18.1": "Q14.2_2",
    "Q19.1": "Q9.1_3",
    "Q20.1": "Q10.2_3",
    "Q21.1": "Q10.2_4",
    "Q22.1": "Q10.2_5",
    "Q23.1": "Q10.2_6",
    "Q24.1": "Q10.2_7",
    "Q25.1": "Q11.2_1",
    "Q26.1": "Q12.1_3",
    "Q27.1": "Q12.1_5",
    "Q28.1": "Q14.1_1",
    "Q29.1": "Q14.2_5",
}

PROMPT_QUESTION_RE = re.compile(
    "You originally rated \(\${e://Field/(?P<question>Q[1-9][0-9]?\.[0-9_]+)}\). The chart below shows everyone's responses."
)
SLIDER_QUESTION_RE = re.compile(
    "You can change your rating below. Select your original "
    "rating \(\$\{e://Field/(?P<question>Q[1-9][0-9]?\.[0-9_]+)}\) to leave it unchanged."
)


def get_extended_mapping():
    extended_mapping = {**t2_to_t1_mapping}
    for k, v in t2_to_t1_mapping.items():
        slider_question_tag = k.replace(".1", ".2")
        extended_mapping[slider_question_tag] = v
    return extended_mapping


def main():
    logger = get_logger()
    survey_client = SurveyDefinitionsClient(survey_id=SURVEY_ID)
    survey = survey_client.get_survey()["result"]
    questions = survey["Questions"]
    t2_to_t1_extended_mapping = get_extended_mapping()
    for k, v in questions.items():
        export_tag = v["DataExportTag"]
        question_text = v["QuestionText"]
        if export_tag in t2_to_t1_extended_mapping:
            if (m := PROMPT_QUESTION_RE.search(question_text)) or (
                m := SLIDER_QUESTION_RE.search(question_text)
            ):
                logger.debug(
                    "Expected substitution",
                    extra={
                        "before": m.group("question"),
                        "after": t2_to_t1_extended_mapping[export_tag],
                    },
                )
                v["QuestionText"] = question_text.replace(
                    m.group("question"), t2_to_t1_extended_mapping[export_tag]
                )
                survey_client.update_question(question_id=k, data=v)
            else:
                logger.error(
                    f"No match for regular expressions found in question {export_tag}",
                    extra={"question_text": question_text},
                )
        else:
            print(f"Skipped question: {question_text}")

    # print list of t1 questions that we need as embedded data
    pprint(sorted(list(t2_to_t1_mapping.values())))


if __name__ == "__main__":
    main()
