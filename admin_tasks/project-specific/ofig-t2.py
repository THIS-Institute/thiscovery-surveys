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
import re
from copy import deepcopy
from pprint import pprint
from thiscovery_lib.qualtrics import SurveyDefinitionsClient
from thiscovery_lib.utilities import get_logger
from local.secrets import OFIG_SURVEY_ID as SURVEY_ID
from admin_tasks.highcharts.make_charts import get_graph_js_for_qualtrics

HIGHCHARTS_CONTAINER = '<div id="{}" style="">Loading....</div>'

QUALTRICS_EMPTY_JS = """Qualtrics.SurveyEngine.addOnload(function()
{
	/*Place your JavaScript here to run when the page loads*/

});

Qualtrics.SurveyEngine.addOnReady(function()
{
	/*Place your JavaScript here to run when the page is fully displayed*/

});

Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/

});"""


t2_to_t1_mapping = {
    "Q2.3": "Q3.3_1",
    "Q3.2": "Q4.2_1",
    "Q3.3": "Q4.4_1",
    "Q3.4": "Q4.8_1",
    "Q3.6": "Q4.10_1",
    "Q4.2": "Q5.2_1",
    "Q4.4": "Q5.4_1",
    "Q4.6": "Q5.6_1",
    "Q4.8": "Q5.8_1",
    "Q5.2": "Q6.2_1",
    "Q5.4": "Q6.4_1",
    "Q5.5": "Q6.6_1",
    "Q5.7": "Q6.8_1",
    "Q5.9": "Q6.10_1",
    "Q5.10": "Q6.12_1",
    "Q6.2": "Q7.2_1",
    "Q6.3": "Q7.4_1",
    "Q7.2": "Q8.6_1",
    "Q7.3": "Q8.8_1",
    "Q7.5": "Q8.10_1",
    "Q7.7": "Q8.14_1",
    "Q8.2": "Q9.4_1",
    "Q8.4": "Q9.6_1",
    "Q8.5": "Q9.8_1",
    "Q8.7": "Q9.10_1",
    "Q9.2": "Q10.4_1",
    "Q10.2": "Q11.4_1",
    "Q10.4": "Q11.6_1",
    "Q10.6": "Q11.8_1",
    "Q11.2": "Q12.2_1",
    "Q11.4": "Q12.4_1",
}

previous_score_re = re.compile(
    "In the first survey, you rated the priority of this operational failure for improvement work as "
    "<b>\(\${e://Field/(?P<question>Q[1-9][0-9]?\.[0-9_]+)}\)</b>"
)

no_consensus_re = re.compile(
    '<div class="qualtrics-question-failed">(.{300,400})not achieved on the <b>importance of prioritising</b> this issue',
    re.DOTALL,
)
no_consensus_target = (
    '<div class="qualtrics-question-failed"><div class="qualtrics-question-failed-icon">'
    '<img src="https://www.thiscovery.org/wp-content/themes/thiscovery/img/cross.svg" alt=""></div><div><span>'
    '<div class="tooltip">Consensus<span class="tooltiptext">Consensus is defined as 80% of responses falling one '
    "rating above or below the median value</span></div> not achieved on the <b>importance of prioritising</b> this issue"
)

consensus_reached_re = re.compile(
    '<div class="qualtrics-question-completed">(.{300,400})achieved on the <b>importance of prioritising</b> this issue\s*</span>\s*</div>\s*</div>',
    re.DOTALL,
)

consensus_reached_target = """
<div class="qualtrics-question-completed">
    <div class="qualtrics-question-completed-icon">
        <img src="https://www.thiscovery.org/wp-content/themes/thiscovery/img/icon-tick-white.svg" alt="">
    </div>
    <span>
        <div class="tooltip">Consensus
            <span class="tooltiptext">Consensus is defined as 80% of responses falling one rating above or below the median value</span>
        </div> achieved on the <b>importance of prioritising</b> this issue
    </span>
</div>
"""


js_add_on_ready_re = re.compile(
    "Qualtrics\.SurveyEngine\.addOnReady\(function\(\)\n?\{"
)


highcharts_placeholder_re_1 = re.compile(
    '<div id="highcharts-(?P<graph_id>[\w-]+)" class="[\w-]+"></div>'
)


highcharts_placeholder_re_2 = re.compile("INSERT GRAPH HERE\.")


def main(dry_run):
    dry_run_postfix = ""
    if dry_run:
        dry_run_postfix = (
            "(this was a dry run, so no changes were actually made to the survey)"
        )
    logger = get_logger()
    survey_client = SurveyDefinitionsClient(survey_id=SURVEY_ID)
    survey = survey_client.get_survey()["result"]
    questions = survey["Questions"]
    updated_questions = list()
    for k, v in questions.items():
        updated_question = False
        export_tag = v["DataExportTag"]
        question_text = v["QuestionText"]

        # replace consensus modals by tooltip
        no_consensus_replacements = no_consensus_re.subn(
            no_consensus_target, question_text
        )
        consensus_reached_replacements = consensus_reached_re.subn(
            consensus_reached_target, question_text
        )
        total_replacements = (
            no_consensus_replacements[1] + consensus_reached_replacements[1]
        )
        if total_replacements > 0:
            if no_consensus_replacements[1] > 0:
                div_name = "Consensus failed"
                question_text = no_consensus_replacements[0]
            elif consensus_reached_replacements[1] > 0:
                div_name = "Consensus reached"
                question_text = consensus_reached_replacements[0]
            logger.info(f"{div_name} div replaced in question {export_tag}", extra={})
            updated_question = True

        # add t1 question scores and graphs
        if export_tag in t2_to_t1_mapping:
            # question scores
            if (m := previous_score_re.search(question_text)) :
                question_text = question_text.replace(
                    m.group("question"), t2_to_t1_mapping[export_tag]
                )
            else:
                logger.error(
                    f"No match for previous score regular expression found in question {export_tag}",
                    extra={"question_text": question_text},
                )

            # graphs
            # add question JS
            existing_question_js = v.get("QuestionJS")
            if not existing_question_js:
                existing_question_js = QUALTRICS_EMPTY_JS
            split_js = js_add_on_ready_re.split(existing_question_js, maxsplit=1)
            assert (
                n := len(split_js)
            ) == 2, f"Unexpected split of existing_question_js ({n}): {split_js}"
            t1_tag = t2_to_t1_mapping[export_tag]
            v["QuestionJS"] = (
                split_js[0]
                + "Qualtrics.SurveyEngine.addOnReady(function()\n{"
                + get_graph_js_for_qualtrics(t1_tag)
                + split_js[1]
            )
            # add graph container
            container_id = f"highcharts-{t1_tag}"
            replacements_1 = highcharts_placeholder_re_1.subn(
                HIGHCHARTS_CONTAINER.format(container_id), question_text
            )
            replacements_2 = highcharts_placeholder_re_2.subn(
                HIGHCHARTS_CONTAINER.format(container_id), question_text
            )
            total_replacements = replacements_1[1] + replacements_2[1]
            assert (
                total_replacements == 1
            ), f"Unexpected number of replacements ({total_replacements}) in question_text: {question_text}"
            replacements = replacements_1
            if replacements_2[1] > 0:
                replacements = replacements_2
            v["QuestionText"] = replacements[0]
            updated_question = True

        if updated_question:
            updated_questions.append(export_tag)
            if not dry_run:
                survey_client.update_question(question_id=k, data=v)
    print(
        f"Updated {len(updated_questions)} questions: {updated_questions} {dry_run_postfix}"
    )


if __name__ == "__main__":
    main(dry_run=True)
