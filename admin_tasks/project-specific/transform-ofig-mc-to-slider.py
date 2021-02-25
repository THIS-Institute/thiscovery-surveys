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

SURVEY_ID = 'SV_9uhyyPy12OLvCMm'
IMPORTANT_QUESTION_RE = '<div><center>How <strong>important is'
EASY_QUESTION_RE_1 = '<div><center>How <strong>easy</strong>'
EASY_QUESTION_RE_2 = '<center><div>How <strong>easy</strong>'

important_question_target = {
    'ChoiceOrder': [1],
    'Choices': {'1': {'Display': '<div>How <strong><div '
                                 'class="tooltip">important<span '
                                 'class="tooltiptext">how '
                                 'important do you think '
                                 'it is to prioritise '
                                 'this issue in future '
                                 'research studies '
                                 'looking at how to '
                                 "improve GPs' work "
                                 'environments?</span></div> '
                                 'is it to '
                                 'prioritise</strong> '
                                 'this problem for '
                                 'improvement?</div>'}},
    'Configuration': {'CSSliderMax': 9,
                      'CSSliderMin': 1,
                      'CustomStart': True,
                      'GridLines': 8,
                      'MobileFirst': True,
                      'NotApplicable': False,
                      'NumDecimals': '0',
                      'QuestionDescriptionOption': 'UseText',
                      'ShowValue': True,
                      'SliderStartPositions': {'1': 0.5},
                      'SnapToGrid': False},
    'DataExportTag': 'Q3.3',
    'DataVisibility': {'Hidden': False, 'Private': False},
    'DefaultChoices': False,
    'GradingData': [],
    'Labels': {'1': {'Display': 'Not important at all'},
               '2': {'Display': 'Neutral'},
               '3': {'Display': 'Extremely important'}},
    'Language': [],
    'NextAnswerId': 4,
    'NextChoiceId': 2,
    'QuestionDescription': 'You find that a piece of '
                           'equipment or item you need '
                           'is missing or broken (eg '
                           'tongue depressor, sp...',
    'QuestionID': 'QID200',
    'QuestionText': '<div class="ofig-question">\n'
                    '<h3>You find that a piece of '
                    'equipment or item you need is '
                    'missing or broken (eg tongue '
                    'depressor, speculum, auroscope or '
                    'thermometer cover, urine/stool '
                    'container, printer paper, '
                    'lubricant, hand gel, faecal occult '
                    'blood test etc.).</h3>\n'
                    '</div>',
    'QuestionText_Unsafe': '<div class="ofig-question">\n'
                           '<h3>You find that a piece of '
                           'equipment or item you need '
                           'is missing or broken (eg '
                           'tongue depressor, speculum, '
                           'auroscope or thermometer '
                           'cover, urine/stool '
                           'container, printer paper, '
                           'lubricant, hand gel, faecal '
                           'occult blood test '
                           'etc.).</h3>\n'
                           '</div>',
    'QuestionType': 'Slider',
    'Selector': 'HSLIDER',
    'Validation': {'Settings': {'ForceResponse': 'OFF',
                                'ForceResponseType': 'ON',
                                'Type': 'None'}}}

easy_question_target = {
    'ChoiceOrder': [1],
    'Choices': {'1': {'Display': '<div>How <strong><div '
                                 'class="tooltip">easy<span '
                                 'class="tooltiptext">How '
                                 'easy do you think it '
                                 'would be to find '
                                 'improvements to this '
                                 'issue that could be '
                                 'applied across '
                                 'different general '
                                 'practice '
                                 'settings?</span></div></strong> '
                                 'would it be to make '
                                 'improvements for this '
                                 'problem?</div>'}},
    'Configuration': {'CSSliderMax': 9,
                      'CSSliderMin': 1,
                      'CustomStart': True,
                      'GridLines': 8,
                      'MobileFirst': True,
                      'NotApplicable': False,
                      'NumDecimals': '0',
                      'QuestionDescriptionOption': 'UseText',
                      'ShowValue': True,
                      'SliderStartPositions': {'1': 0.4994974874371859},
                      'SnapToGrid': False},
    'DataExportTag': 'Q3.4',
    'DataVisibility': {'Hidden': False, 'Private': False},
    'DefaultChoices': False,
    'GradingData': [],
    'Labels': {'1': {'Display': 'Not easy at all'},
               '2': {'Display': 'Neutral'},
               '3': {'Display': 'Extremely easy'}},
    'Language': [],
    'NextAnswerId': 4,
    'NextChoiceId': 10,
    'QuestionDescription': 'How easy would it be to make '
                           'improvements for this '
                           'problem?',
    'QuestionID': 'QID90',
    'QuestionText': '<div style="display: none">How '
                    '<strong>easy</strong> would it be to '
                    'make improvements for this '
                    'problem?</div>',
    'QuestionText_Unsafe': '<div style="display: '
                           'none">How '
                           '<strong>easy</strong> would '
                           'it be to make improvements '
                           'for this problem?</div>',
    'QuestionType': 'Slider',
    'Selector': 'HSLIDER',
    'Validation': {'Settings': {'ForceResponse': 'OFF',
                                'ForceResponseType': 'ON',
                                'Type': 'None'}}}


def _preserve_attributes(question, target):
    updated_question = deepcopy(target)
    attributes_to_preserve = [
        'DataExportTag',
        'QuestionDescription',
        'QuestionID'
    ]
    for attribute in attributes_to_preserve:
        updated_question[attribute] = question[attribute]
    return updated_question


def parse_important_question(question):
    updated_question = _preserve_attributes(question, important_question_target)
    attributes_to_edit = [
        'QuestionText',
        'QuestionText_Unsafe',
    ]
    for attribute in attributes_to_edit:
        updated_question[attribute] = question[attribute].split(IMPORTANT_QUESTION_RE)[0]
    return updated_question


def parse_easy_question(question):
    return _preserve_attributes(question, easy_question_target)


def main():
    survey_client = SurveyDefinitionsClient(survey_id=SURVEY_ID)
    survey = survey_client.get_survey()['result']
    questions = survey['Questions']
    for k, v in questions.items():
        question_text = v['QuestionText']
        updated_question = None
        if IMPORTANT_QUESTION_RE in question_text:
            updated_question = parse_important_question(v)
        elif (EASY_QUESTION_RE_1 in question_text) or (EASY_QUESTION_RE_2 in question_text):
            updated_question = parse_easy_question(v)
        else:
            print(f'Skipped question: {question_text}')

        if updated_question:
            survey_client.update_question(question_id=k, data=updated_question)


if __name__ == '__main__':
    main()
