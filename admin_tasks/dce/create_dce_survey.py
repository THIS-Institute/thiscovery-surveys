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
import csv
import thiscovery_lib.qualtrics as qs
import thiscovery_lib.utilities as utils
from copy import deepcopy
from pprint import pprint
from thiscovery_dev_tools.scripting_tools import CsvImporter


DEFAULT_SURVEY = "SV_1QSx0QCbx1ZaLK6"
# input file details
BLOCK_NAME = 'Block'
SCENARIO_NAME = 'Scenario'
OPTION_NAME = 'Option'
NON_ATTRIBUTE_COLUMNS = [
    BLOCK_NAME,
    SCENARIO_NAME,
    OPTION_NAME,
    'UID',
    'Choice situation',
]


class NamedDceElement:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return str(self.__dict__)


class DceBlock(NamedDceElement):
    """
    Represents a block of scenarios in a DCE.
    Contains scenarios.
    Implemented as a Qualtrics group.
    """
    def __init__(self, name):
        super().__init__(name=name)
        self.scenarios = dict()


class DceScenario(NamedDceElement):
    """
    Represents a scenario in a DCE.
    Contains options.
    Implemented as a Qualtrics block containing 1 question.
    """
    def __init__(self, name):
        super().__init__(name=name)
        self.options = dict()


class DceOption(NamedDceElement):
    """
    Represents an option in a DCE.
    Contains attributes.
    Rows in input csv file are options.
    Implemented as part of the question text in Qualtrics
    """
    def __init__(self, name):
        super().__init__(name=name)
        self.levels = dict()


class DceAttribute:
    """
    Represents an attribute in a DCE.
    Contains attribute levels
    Implemented as part of the question text in Qualtrics
    """
    pass


class DceLevel:
    """
    Represents an attribute level in a DCE.
    Implemented as part of the question text in Qualtrics
    """
    pass


class DceSurveyManager(CsvImporter):
    """
    Manages the process of creating/updating DCE surveys
    """
    qualtrics_question_template = {
        "QuestionText": None,
        "DataExportTag": None,  # "Q1"
        "QuestionType": "MC",
        "Selector": "SAVR",
        "SubSelector": "TX",
        "Configuration": {"QuestionDescriptionOption": "UseText", "Autoscale": {"YScale": {"Name": "yesNo", "Type": "likert", "Reverse": False}}},
        "Choices": {"1": {"Display": "yes"}, "2": {"Display": "no"}},
        "ChoiceOrder": ["1", "2"],
        "Validation": {"Settings": {"ForceResponse": "OFF", "ForceResponseType": "ON", "Type": "None"}},
        "Language": [],
        # "QuestionID": "QID1",  Note: question ID cannot be set via the API
        "DataVisibility": {"Private": False, "Hidden": False},
    }

    def __init__(self, survey_id=None, survey_name=None, input_dataset=None):
        super().__init__(csvfile_path=input_dataset)
        self.survey_client = qs.SurveyDefinitionsClient(survey_id=survey_id)

        if survey_id is None:
            if survey_name == "Test survey":
                from random import randrange
                survey_name = f"Test survey {randrange(99999)}"
            self.survey_client.create_survey(survey_name)
            print(f"Created new survey: {survey_name}")

        self.survey = self.survey_client.get_survey()['result']
        pprint(self.survey)

        self.groups = dict()  # using Qualtrics terminology here; same as DCE blocks
        self.groups_to_update = dict()
        self.groups_to_add = dict()
        self.groups_to_delete = dict()
        self.groups_not_to_touch = dict()

        self.blocks_to_update = dict()  # using Qualtrics terminology here; similar to DCE scenario
        self.blocks_to_add = dict()
        self.blocks_to_delete = dict()
        self.blocks_not_to_touch = dict()

        self.questions_to_update = dict()  # using Qualtrics terminology here; similar to DCE scenario
        self.questions_to_add = dict()
        self.questions_to_delete = dict()
        self.questions_not_to_touch = dict()

    def parse_input_csv(self):
        with open(self.input_filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                block_name = row[BLOCK_NAME]
                scenario_name = row[SCENARIO_NAME]
                scenario_id = f'{block_name}.{scenario_name}'
                option_name = row[OPTION_NAME]
                option_id = f'{scenario_id}.{option_name}'
                try:
                    block = self.groups[block_name]
                except KeyError:
                    block = DceBlock(name=block_name)
                try:
                    scenario = block.scenarios[scenario_id]
                except KeyError:
                    scenario = DceScenario(name=scenario_id)
                option = DceOption(name=option_id)

                # iterate through attributes
                for k, v in row.items():
                    if k in NON_ATTRIBUTE_COLUMNS:
                        continue
                    option.levels.update({k: v})

                scenario.options.update({option_id: option})
                block.scenarios.update({scenario_id: scenario})
                self.groups.update({block_name: block})

    def parse_scenarios(self, interactive=False):
        """
        Args:
            interactive: If True, asks for confirmation of changes before applying to survey

        Returns:
            Tuple of responses (dict objects) of requests to add, update and delete questions:
            (add_responses, update_responses, delete_responses)
        """
        def covert_key_from_id_to_tag(questions):
            return {v["DataExportTag"]: v for _, v in questions.items()}

        def question_text_is_identical(q1, q2):
            return q1["QuestionText"] == q2["QuestionText"]

        if self.survey['Questions']:
            existing_questions = covert_key_from_id_to_tag(self.survey['Questions'])
        else:
            existing_questions = dict()
        self.questions_to_delete = {k: v for k, v in existing_questions.items()}
        for group in [self.input_questions, self.comment_box_questions]:
            for k, v in group.items():
                if k not in existing_questions.keys():
                    self.questions_to_add[k] = v
                else:
                    del self.questions_to_delete[k]
                    v["QuestionID"] = existing_questions[k]["QuestionID"]
                    if not question_text_is_identical(v, existing_questions[k]):
                        self.questions_to_update[k] = v
                    else:
                        self.questions_not_to_touch[k] = v

        for verb, question_dict in [('add', self.questions_to_add), ('update', self.questions_to_update),
                                    ('delete', self.questions_to_delete), ('leave untouched', self.questions_not_to_touch)]:
            print(f"{len(question_dict.keys())} questions to {verb}:")
            for _, v in question_dict.items():
                print(f"QuestionID: {v.get('QuestionID')}; DataExportTag: {v['DataExportTag']}; question: {v}\n")
            print("\n")

        if interactive:
            i = input("Would you like to apply the changes above? [y/N]")
            if i not in ['y', 'Y']:
                print('No changes applied to survey')
                return None

        add_responses = self.add_questions()
        logger.info('Responses from self.add_questions', extra={'responses': add_responses})
        update_responses = self.update_questions()
        logger.info('Responses from self.update_questions', extra={'responses': update_responses})
        delete_responses = self.delete_questions()
        logger.info('Responses from self.delete_questions', extra={'responses': delete_responses})

        # update added questions with Qualtrics QuestionID
        for k, v in add_responses.items():
            question = self.questions_to_add[k]
            question['QuestionID'] = v['result']['QuestionID']

        return add_responses, update_responses, delete_responses


if __name__ == "__main__":
    """
    Pass either survey_id to update an existing survey or survey_name to create a new survey.
    If survey_name == "Test survey", the survey created will be named "Test survey XXXXX", where
    XXXXX is a random 5 digit integer. 
    """
    manager = DceSurveyManager(
        survey_id=DEFAULT_SURVEY,
        input_dataset="SP1_health_care_options.csv"
    )
    manager.parse_input_csv()
