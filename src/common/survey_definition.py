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
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.qualtrics import SurveyDefinitionsClient

import common.constants as const


PROMPT_RE = re.compile('<div class="prompt">(.+)</div>')
DESCRIPTION_RE = re.compile('<div class="description">(.+)</div>')


class InterviewQuestion:
    """
    Represents an item in InterviewQuestions ddb table
    """
    def __init__(self, **kwargs):
        self._survey_id = kwargs.get('survey_id')  # partition key
        self._question_id = kwargs.get('question_id')  # sort key
        self.survey_modified = kwargs.get('survey_modified')
        self.question_name = kwargs.get('question_name')
        self.sequence_no = kwargs.get('sequence_no')
        self.block_name = kwargs.get('block_name')
        self.block_id = kwargs.get('block_id')
        self.question_text = kwargs.get('question_text')
        self.question_description = kwargs.get('question_description')

    def as_dict(self):
        d = {k: v for k, v in self.__dict__.items() if (k[0] != "_") and (k not in ['created', 'modified'])}
        return d

    def __repr__(self):
        return str(self.as_dict())


class SurveyDefinition:

    def __init__(self, qualtrics_account_name='cambridge', survey_id=None, correlation_id=None):
        client = SurveyDefinitionsClient(
            qualtrics_account_name=qualtrics_account_name,
            survey_id=survey_id,
            correlation_id=correlation_id,
        )
        response = client.get_survey()
        assert response['meta']['httpStatus'] == '200 - OK', f'Call to Qualtrics API failed with response {response}'
        self.survey_id = survey_id
        self.definition = response['result']
        self.flow = self.definition['SurveyFlow']['Flow']
        self.blocks = self.definition['Blocks']
        self.questions = self.definition['Questions']
        self.modified = self.definition['LastModified']
        self.ddb_client = Dynamodb(stack_name=const.STACK_NAME)

    def get_interview_question_list(self):

        def parse_question_html(s):
            text_m = PROMPT_RE.search(s)
            try:
                text = text_m.group(1)
            except AttributeError:
                text = None

            description_m = DESCRIPTION_RE.search(s)
            try:
                description = description_m.group(1)
            except AttributeError:
                description = None
            return text, description

        interview_question_list = list()
        question_counter = 0
        block_ids_flow = [x['ID'] for x in self.flow]
        for block_id in block_ids_flow:
            block = self.blocks[block_id]
            block_name = block['Description']
            question_ids = [x['QuestionID'] for x in block['BlockElements']]
            for question_id in question_ids:
                question_counter += 1
                q = self.questions[question_id]
                question_name = q['DataExportTag']
                question_text, question_description = parse_question_html(q['QuestionText'])
                question = InterviewQuestion(
                    survey_id=self.survey_id,
                    survey_modified=self.modified,
                    question_id=question_id,
                    question_name=question_name,
                    sequence_no=question_counter,
                    block_name=block_name,
                    block_id=block_id,
                    question_text=question_text,
                    question_description=question_description,
                )
                interview_question_list.append(question)
        return interview_question_list

    def ddb_dump_interview_questions(self):
        question_list = self.get_interview_question_list()
        for q in question_list:
            self.ddb_client.put_item(
                table_name=const.INTERVIEW_QUESTIONS_TABLE,
                key=q._survey_id,
                key_name='survey_id',
                item_type='interview_question',
                item_details=None,
                item=q.as_dict(),
                update_allowed=True,
                sort_key={
                    'question_id': q._question_id,
                },
            )









