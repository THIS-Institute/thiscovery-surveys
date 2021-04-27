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
import re
import regex
from pprint import pprint
from thiscovery_lib.qualtrics import SurveyDefinitionsClient
from thiscovery_lib.utilities import get_logger
from local.secrets import HFPEF_SURVEY_ID as SURVEY_ID


logger = get_logger()


def main(dry_run=False):
    dry_run_postfix = ""
    if dry_run:
        dry_run_postfix = (
            "(this was a dry run, so no changes were actually made to the survey)"
        )
    survey_client = SurveyDefinitionsClient(survey_id=SURVEY_ID)
    survey = survey_client.get_survey()["result"]
    questions = survey["Questions"]

    # fix graphs
    highcharts_re = re.compile('<div id="highcharts-(?P<graph_id>[\w-]+)"')
    everviz_script_re = re.compile(
        '<script src="https://app.everviz.com/inject/[\w-]+/" defer="defer"></script>'
    )
    target_script = '<script src="https://app.everviz.com/inject/{graph_id}/" defer="defer"></script>'

    updated_questions_counter = 0
    updated_questions_tags = list()
    graph_questions = (
        list()
    )  # list of tuples: (question_id, question, graph_id, DataExportTag, everviz_script)
    for k, v in questions.items():
        question_text = v["QuestionText"]
        tag = v["DataExportTag"]
        if (graph_m := highcharts_re.search(question_text)) :
            everviz_script = None
            if (script_m := everviz_script_re.search(question_text)) :
                everviz_script = script_m.group()
            graph_questions.append(
                (k, v, graph_m.group("graph_id"), tag, everviz_script)
            )
    print(
        f'Graphs detected in {len(graph_questions)} questions: {", ".join([x[3] for x in graph_questions])}'
    )
    print(
        f'Everviz script missing in {len((problem_questions := [x for x in graph_questions if x[4] is None]))} questions: {", ".join([x[3] for x in problem_questions])}'
    )

    if problem_questions:
        for k, v, graph_id, tag, _ in problem_questions:
            v["QuestionText"] += target_script.format(graph_id=graph_id)
            updated_questions_counter += 1
            updated_questions_tags.append(tag)
            if not dry_run:
                survey_client.update_question(question_id=k, data=v)
    print(
        f"Highcharts graph fixed in {updated_questions_counter} questions {dry_run_postfix}"
    )
    # print(f"Here are their tags: {updated_questions_tags}")


if __name__ == "__main__":
    main(dry_run=True)
