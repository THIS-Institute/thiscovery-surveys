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
import thiscovery_lib.utilities as utils
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.qualtrics import SurveyDefinitionsClient

import common.constants as const


PROMPT_RE = re.compile('<div class="prompt">(.+)</div>')
DESCRIPTION_RE = re.compile('<div class="description">(.+)</div>')
SYSTEM_RE = re.compile('<div class="system">(.+)</div>')


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
        self.logger = utils.get_logger()
        self.logger.debug('Initialised SurveyDefinition', extra={
            '__dict__': self.__dict__,
            'correlation_id': correlation_id,
        })

    @classmethod
    def from_eb_event(cls, event):
        logger = utils.get_logger()
        logger.debug('EB event', extra={
            'event': event,
        })
        event_detail = event['detail']
        try:
            qualtrics_account_name = event_detail.pop('account')
            survey_id = event_detail.pop('survey_id')
        except KeyError as exc:
            raise utils.DetailedValueError(
                f'Mandatory {exc} data not found in source event',
                details={
                    'event': event,
                }
            )
        return cls(
            qualtrics_account_name=qualtrics_account_name,
            survey_id=survey_id,
            correlation_id=event['id']
        )

    def get_interview_question_list_from_Qualtrics(self):

        def parse_question_html(s):
            text_m = PROMPT_RE.search(s)
            text = text_m.group(1)

            description_m = DESCRIPTION_RE.search(s)
            try:
                description = description_m.group(1)
            except AttributeError:
                description = None
            return text, description

        interview_question_list = list()
        question_counter = 1
        block_ids_flow = [x['ID'] for x in self.flow if x['Type'] not in ['Branch']]  # flow items of Branch type represent survey branching logic
        for block_id in block_ids_flow:
            block = self.blocks[block_id]
            block_name = block['Description']
            question_ids = [x['QuestionID'] for x in block['BlockElements']]
            for question_id in question_ids:
                q = self.questions[question_id]
                question_name = q['DataExportTag']
                question_text_raw = q['QuestionText']
                try:
                    question_text, question_description = parse_question_html(question_text_raw)
                except AttributeError:  # no match found for PROMPT_RE
                    if SYSTEM_RE.findall(question_text_raw):
                        continue  # this is a system config question; skip
                    else:
                        raise utils.DetailedValueError(
                            'Mandatory prompt div could not be found in interview question',
                            details={
                                'question': question_text_raw,
                                'survey_id': self.survey_id,
                                'question_id': question_id,
                                'question_export_tag': question_name,
                            }
                        )
                question = InterviewQuestion(
                    survey_id=self.survey_id,
                    survey_modified=self.modified,
                    question_id=question_id,
                    question_name=question_name,
                    sequence_no=str(question_counter),
                    block_name=block_name,
                    block_id=block_id,
                    question_text=question_text,
                    question_description=question_description,
                )
                interview_question_list.append(question)
                question_counter += 1
        return interview_question_list

    def ddb_update_interview_questions(self):
        """
        Updates the list of interview questions held in Dynamodb for a particular survey.
        This includes not only adding and updating questions, but also deleting questions that are no longer
        present in the survey
        """
        ddb_question_list = self.ddb_load_interview_questions(self.survey_id)
        survey_question_list = self.get_interview_question_list_from_Qualtrics()
        updated_question_ids = list()
        deleted_question_ids = list()
        for q in survey_question_list:
            self.ddb_client.put_item(
                table_name=const.INTERVIEW_QUESTIONS_TABLE['name'],
                key=q._survey_id,
                key_name=const.INTERVIEW_QUESTIONS_TABLE['partition_key'],
                item_type='interview_question',
                item_details=None,
                item=q.as_dict(),
                update_allowed=True,
                sort_key={
                    const.INTERVIEW_QUESTIONS_TABLE['sort_key']: q._question_id,
                },
            )
            updated_question_ids.append(q._question_id)

        for q in ddb_question_list:
            question_id = q['question_id']
            if question_id not in updated_question_ids:
                self.ddb_client.delete_item(
                    table_name=const.INTERVIEW_QUESTIONS_TABLE['name'],
                    key=q['survey_id'],
                    key_name=const.INTERVIEW_QUESTIONS_TABLE['partition_key'],
                    sort_key={
                        const.INTERVIEW_QUESTIONS_TABLE['sort_key']: question_id,
                    },
                )
                deleted_question_ids.append(question_id)

        return updated_question_ids, deleted_question_ids

    @staticmethod
    def ddb_load_interview_questions(survey_id):
        ddb_client = Dynamodb(stack_name=const.STACK_NAME)
        return ddb_client.query(
            table_name=const.INTERVIEW_QUESTIONS_TABLE['name'],
            KeyConditionExpression='survey_id = :survey_id',
            ExpressionAttributeValues={
                ':survey_id': survey_id,
            }
        )

    @staticmethod
    def get_interview_questions(survey_id):
        interview_questions = SurveyDefinition.ddb_load_interview_questions(survey_id)

        try:
            survey_modified = interview_questions[0]['survey_modified']
        except IndexError:
            raise utils.ObjectDoesNotExistError(f'No interview questions found for survey {survey_id}', details={})

        block_dict = dict()
        for iq in interview_questions:
            block_id = iq['block_id']

            try:
                block = block_dict[block_id]
            except KeyError:
                block = {
                    'block_id': block_id,
                    'block_name': iq['block_name'],
                    'questions': list(),
                }

            question = {
                'question_id': iq['question_id'],
                'question_name': iq['question_name'],
                'sequence_no': iq['sequence_no'],
                'question_text': iq['question_text'],
                'question_description': iq['question_description'],
            }

            block['questions'].append(question)
            block_dict[block_id] = block

        body = {
            'survey_id': survey_id,
            'modified': survey_modified,
            'blocks': list(block_dict.values()),
            'count': len(interview_questions),
        }

        return body
