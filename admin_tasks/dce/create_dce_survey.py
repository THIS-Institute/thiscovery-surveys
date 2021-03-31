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
import jinja2 as j2
import thiscovery_lib.qualtrics as qs
import thiscovery_lib.utilities as utils
from copy import deepcopy
from thiscovery_dev_tools.scripting_tools import CsvImporter

# input file details
BLOCK_NAME = "Block"
SCENARIO_NAME = "Scenario"
OPTION_NAME = "Option"
NON_ATTRIBUTE_COLUMNS = [
    BLOCK_NAME,
    SCENARIO_NAME,
    OPTION_NAME,
    "UID",
    "Choice situation",
]

qualtrics_multiplechoice_question_template = {
    "QuestionText": "Which option would you choose?",
    "DataExportTag": None,  # "Q1"
    "QuestionType": "MC",
    "Randomization": {"Advanced": None, "TotalRandSubset": "", "Type": "All"},
    "Selector": "SAHR",
    "SubSelector": "TX",
    "Configuration": {"LabelPosition": "BELOW", "QuestionDescriptionOption": "UseText"},
    "Choices": {"1": {"Display": "yes"}, "2": {"Display": "no"}},
    "ChoiceOrder": ["1", "2"],
    "Validation": {
        "Settings": {"ForceResponse": "OFF", "ForceResponseType": "ON", "Type": "None"}
    },
    "Language": [],
    # "QuestionID": "QID1",  Note: question ID cannot be set via the API
    "DataVisibility": {"Private": False, "Hidden": False},
}

qualtrics_block_template = {
    "Type": "Standard",
    "Description": "Untitled block",
    "BlockElements": [
        {"Type": "Question", "QuestionID": None},
        {"Type": "Question", "QuestionID": None},
    ],
}

warning_counter = 0
logger = utils.get_logger()
env = j2.Environment(
    loader=j2.FileSystemLoader("."),
)
dce_question_template = env.get_template("dce_question_table.j2")
dce_choice_template = env.get_template("dce_choice.j2")


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

    def _rendered_qualtrics_question_text(self):
        header = ["Attribute"]
        attributes_and_levels = dict()
        option_counter = 0
        for k, v in self.options.items():
            option_counter += 1
            header.append(f"Option {option_counter}")
            for attribute, level in v.levels.items():
                try:
                    attribute_levels = attributes_and_levels["attribute"]
                except KeyError:
                    attribute_levels = list()
                attribute_levels.append(level)
                attributes_and_levels["attribute"] = attribute_levels
        return dce_question_template.render(
            header=header,
            attributes=attributes_and_levels,
        )

    def _rendered_qualtrics_choices_and_order(self):
        choices = dict()
        choice_order = list()
        attributes_and_levels = dict()
        option_counter = 0
        for k, v in self.options.items():
            option_counter += 1
            choice_header = f"Option {option_counter}"
            choice = dce_choice_template.render(
                choice_header=choice_header,
                attributes=v.levels,
            )

            choice_key = str(option_counter)
            choices[choice_key] = {"Display": choice}
            choice_order.append(choice_key)
        return choices, choice_order

    def rendered_question(self):
        question = deepcopy(qualtrics_multiplechoice_question_template)
        # question["QuestionText"] = self._rendered_qualtrics_question_text()
        (
            question["Choices"],
            question["ChoiceOrder"],
        ) = self._rendered_qualtrics_choices_and_order()
        question["DataExportTag"] = self.name
        # logger.debug('rendered_question', extra=question)
        return question


class DceOption(NamedDceElement):
    """
    Represents an option in a DCE.
    Contains attributes.
    Rows in input csv file are options.
    Implemented as part of the question definition in Qualtrics
    """

    def __init__(self, name):
        super().__init__(name=name)
        self.levels = dict()


class DceSurveyManager(CsvImporter):
    """
    Manages the process of creating/updating DCE surveys
    """

    def __init__(self, survey_id=None, survey_name=None, input_dataset=None):
        super().__init__(csvfile_path=input_dataset)
        self.survey_client = qs.SurveyDefinitionsClient(survey_id=survey_id)

        if survey_id is None:
            if survey_name == "Test survey":
                from random import randrange

                survey_name = f"Test survey {randrange(99999)}"
            self.survey_client.create_survey(survey_name)
            print(f"Created new survey: {survey_name}")

        self.survey = self.survey_client.get_survey()["result"]
        # pprint(self.survey)

        self.groups = dict()  # using Qualtrics terminology here; same as DCE blocks
        self.questions = dict()  # rendered questions indexed by export tag
        self.thrash_block_id = None

        self.blocks_to_update = (
            dict()
        )  # using Qualtrics terminology here; similar to DCE scenario
        self.blocks_to_add = dict()
        self.blocks_to_delete = dict()
        self.blocks_not_to_touch = dict()

        self.questions_to_update = (
            dict()
        )  # using Qualtrics terminology here; similar to DCE scenario
        self.questions_to_add = dict()
        self.questions_to_delete = dict()
        self.questions_not_to_touch = dict()

    def parse_input_csv(self):
        with open(self.input_filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                group_name = row[BLOCK_NAME]
                block_and_question_name = row[SCENARIO_NAME]
                block_and_question_id = f"{group_name}.{block_and_question_name}"
                choice_name = row[OPTION_NAME]
                choice_id = f"{block_and_question_id}.{choice_name}"
                try:
                    group = self.groups[group_name]
                except KeyError:
                    group = DceBlock(name=group_name)
                try:
                    block_and_question = group.scenarios[block_and_question_id]
                except KeyError:
                    block_and_question = DceScenario(name=block_and_question_id)
                choice = DceOption(name=choice_id)

                # iterate through attributes
                for k, v in row.items():
                    if k in NON_ATTRIBUTE_COLUMNS:
                        continue
                    choice.levels.update({k: v})

                block_and_question.options.update({choice_id: choice})
                group.scenarios.update({block_and_question_id: block_and_question})
                self.questions.update({block_and_question_id: block_and_question})
                self.groups.update({group_name: group})

    # region block methods
    def add_blocks(self):
        """
        Qualtrics' "Create block" API method (https://api.qualtrics.com/reference#create-block) does not accept the BlockElements parameter,
        so this function creates the new block without it and then immediately updates it with the required Elements.

        Returns:
            Dictionary of responses from the create and update phases: {'create_response': x, 'update_response': y}
        """
        responses = dict()
        for k, v in self.blocks_to_add.items():
            block_elements = v.pop("BlockElements")
            create_response = self.survey_client.create_block(data=v)
            block_id = create_response["result"]["BlockID"]
            v["BlockElements"] = block_elements
            update_response = self.survey_client.update_block(block_id, data=v)
            responses[k] = {
                "create_response": create_response,
                "update_response": update_response,
            }
        return responses

    def update_blocks(self):
        responses = dict()
        for k, v in self.blocks_to_update.items():
            responses[k] = self.survey_client.update_block(v["ID"], data=v)
        return responses

    def delete_blocks(self):
        pass
        # responses = dict()
        # for k, v in self.blocks_to_delete.items():
        #     responses[k] = self.survey_client.delete_block(v['ID'])
        # return responses

    # endregion

    # region question methods
    def add_questions(self):
        responses = dict()
        for k, q in self.questions_to_add.items():
            responses[k] = self.survey_client.create_question(data=q)
        return responses

    def update_questions(self):
        responses = dict()
        for k, q in self.questions_to_update.items():
            responses[k] = self.survey_client.update_question(q["QuestionID"], data=q)
        return responses

    def delete_questions(self):
        responses = dict()
        for k, q in self.questions_to_delete.items():
            responses[k] = self.survey_client.delete_question(q["QuestionID"])
        return responses

    # endregion

    def parse_questions(self, interactive=False):
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

        if self.survey["Questions"]:
            existing_questions = covert_key_from_id_to_tag(self.survey["Questions"])
        else:
            existing_questions = dict()
        self.questions_to_delete = {k: v for k, v in existing_questions.items()}
        for k, v in self.questions.items():
            rendered_question = v.rendered_question()
            if k not in existing_questions.keys():
                self.questions_to_add[k] = rendered_question
            else:
                del self.questions_to_delete[k]
                rendered_question["QuestionID"] = existing_questions[k]["QuestionID"]
                if not question_text_is_identical(
                    rendered_question, existing_questions[k]
                ):
                    self.questions_to_update[k] = rendered_question
                else:
                    self.questions_not_to_touch[k] = rendered_question

        for verb, question_dict in [
            ("add", self.questions_to_add),
            ("update", self.questions_to_update),
            ("delete", self.questions_to_delete),
            ("leave untouched", self.questions_not_to_touch),
        ]:
            print(f"{len(question_dict.keys())} questions to {verb}:")
            for _, v in question_dict.items():
                print(
                    f"QuestionID: {v.get('QuestionID')}; DataExportTag: {v['DataExportTag']}; question: {v}\n"
                )
            print("\n")

        if interactive:
            i = input("Would you like to apply the changes above? [y/N]")
            if i not in ["y", "Y"]:
                print("No changes applied to survey")
                return None

        add_responses = self.add_questions()
        logger.info(
            "Responses from self.add_questions", extra={"responses": add_responses}
        )
        update_responses = self.update_questions()
        logger.info(
            "Responses from self.update_questions",
            extra={"responses": update_responses},
        )
        delete_responses = self.delete_questions()
        logger.info(
            "Responses from self.delete_questions",
            extra={"responses": delete_responses},
        )

        # update added questions with Qualtrics QuestionID
        for k, v in add_responses.items():
            question = self.questions_to_add[k]
            question["QuestionID"] = v["result"]["QuestionID"]

        return add_responses, update_responses, delete_responses

    def parse_blocks(self):
        def covert_key_from_block_id_to_question_id(blocks, survey_update_manager):
            converted_blocks = dict()
            for k_, v_ in blocks.items():

                # skip the Trash block
                if v_["Type"] == "Trash":
                    logger.debug(f"Skipped Trash block {k_}")
                    survey_update_manager.thrash_block_id = k_
                    continue

                try:
                    converted_blocks[
                        # v_['BlockElements'][0]['QuestionID']
                        v_[
                            "Description"
                        ]  # description also holds the QuestionID and works for empty blocks (that had all their questions deleted)
                    ] = {**v_, "block_id": k_}
                except KeyError:
                    logger.warning(
                        f"Block {k_} was not created by this script; it will be ignored",
                        extra={"block definition": v_},
                    )
                    global warning_counter
                    warning_counter += 1
            return converted_blocks

        def block_elements_are_identical(b1, b2):
            return b1["BlockElements"] == b2["BlockElements"]

        self.survey = self.survey_client.get_survey()[
            "result"
        ]  # question updates can change the structure of the blocks, so refresh self.survey
        existing_blocks = covert_key_from_block_id_to_question_id(
            self.survey["Blocks"], self
        )
        self.blocks_to_delete = deepcopy(existing_blocks)

        main_questions_for_blocks = {
            **self.questions_to_add,
            **self.questions_to_update,
            **self.questions_not_to_touch,
        }
        self.question_ids = [
            v["QuestionID"] for _, v in main_questions_for_blocks.items()
        ]

        for k, v in main_questions_for_blocks.items():
            question_id = v["QuestionID"]
            export_tag = v["DataExportTag"]
            block_elements_dict = {
                "BlockElements": [
                    {"Type": "Question", "QuestionID": question_id},
                ]
            }
            edited_block = deepcopy(qualtrics_block_template)
            edited_block.update({**block_elements_dict, "Description": export_tag})
            if question_id not in existing_blocks.keys():
                self.blocks_to_add[question_id] = edited_block
            else:
                del self.blocks_to_delete[question_id]
                edited_block["ID"] = existing_blocks[question_id]["ID"]
                if not block_elements_are_identical(
                    block_elements_dict, existing_blocks[question_id]
                ):
                    self.blocks_to_update[question_id] = edited_block
                else:
                    self.blocks_not_to_touch[question_id] = edited_block

        for verb, block_dict in [
            ("add", self.blocks_to_add),
            ("update", self.blocks_to_update),
            ("delete", self.blocks_to_delete),
        ]:
            print(f"{len(block_dict.keys())} blocks to {verb}:")
            for _, v in block_dict.items():
                print(
                    f"ID: {v.get('ID')}; BlockElements: {v['BlockElements']}; block: {v}\n"
                )
            print("\n")

        add_responses = self.add_blocks()
        logger.info(
            "Responses from self.add_blocks", extra={"responses": add_responses}
        )
        update_responses = self.update_blocks()
        logger.info(
            "Responses from self.update_blocks", extra={"responses": update_responses}
        )
        delete_responses = self.delete_blocks()
        logger.info(
            "Responses from self.delete_blocks", extra={"responses": delete_responses}
        )

        return add_responses, update_responses, delete_responses

    def parse_flow(self):
        randomiser_template = {
            "EvenPresentation": True,
            "Flow": [],
            "FlowID": "FL_7",
            "SubSet": 1,
            "Type": "BlockRandomizer",
        }
        group_flow_element_template = {
            "Description": "Group 1",
            "Flow": [
                {
                    "Autofill": [],
                    "FlowID": "FL_2",
                    "ID": "BL_b8gLFR4Hbrtu2pM",
                    "Type": "Block",
                }
            ],
            "FlowID": "FL_100",
            "Type": "Group",
        }
        self.survey = self.survey_client.get_survey()[
            "result"
        ]  # question and block updates can change the flow structure so refresh self.survey
        flow_dict = self.survey["SurveyFlow"]
        flow_dict_flow = flow_dict["Flow"]
        blocks_dict = self.survey["Blocks"]
        flow_count = flow_dict["Properties"]["Count"]
        randomiser_flow = list()
        global_group_indexes = list()
        for k, _ in self.groups.items():
            group_flow_element = deepcopy(group_flow_element_template)
            group_blocks = list()
            flow_copy = deepcopy(flow_dict_flow)
            group_indexes = list()
            for block in flow_copy:
                if block["Type"] not in ["Block", "Standard"]:  # not a block
                    continue
                block_id = block["ID"]
                block_description = blocks_dict[block_id]["Description"]
                block_group_number = block_description.split(".")[0]
                if block_group_number == k:
                    group_blocks.append(block)
                    flow_dict_flow.remove(block)
                    index = flow_copy.index(block)
                    group_indexes.append(index)
                    global_group_indexes.append(index)
            flow_count += 1
            group_flow_element.update(
                {
                    "Description": f"DCE block {k}",
                    "Flow": group_blocks,
                    "FlowID": f"FL_{flow_count}",
                }
            )
            randomiser_flow.append(group_flow_element)
        flow_count += 1
        randomiser = {
            **randomiser_template,
            "Flow": randomiser_flow,
            "FlowID": f"FL_{flow_count}",
        }
        flow_dict_flow.insert(global_group_indexes[0], randomiser)
        self.survey_client.update_flow(data=flow_dict)

    def remove_questions_managed_by_this_script_from_thrash_block(self):
        self.survey = self.survey_client.get_survey()["result"]  # refresh self.survey
        thrash_block = self.survey["Blocks"][self.thrash_block_id]
        try:
            edited_block_elements = [
                x
                for x in thrash_block["BlockElements"]
                if x["QuestionID"] not in self.question_ids
            ]
        except KeyError:
            logger.info(
                "Thrash block (bin/unused questions) is empty",
                extra={"trash_block": thrash_block},
            )
        else:
            thrash_block.update({"BlockElements": edited_block_elements})
            return self.survey_client.update_block(
                self.thrash_block_id, data=thrash_block
            )

    def update_survey(self, interactive=False):
        """
        This is the main routine of this class.

        Returns:
            Tuple of responses from the parse questions and parse blocks phases
        """
        parse_questions_results = self.parse_questions(interactive)
        parse_blocks_results = self.parse_blocks()
        parse_flow_results = self.parse_flow()
        cleanup_result = (
            {
                "cleanup_result": self.remove_questions_managed_by_this_script_from_thrash_block()
            },
        )
        return (
            parse_questions_results,
            parse_blocks_results,
            parse_flow_results,
            cleanup_result,
        )


def main(
    survey_id=None,
    survey_name=None,
    input_dataset="SP1_health_care_options.csv",
    interactive=False,
):
    """
    Args:
        survey_id: If None, a new survey will be created; otherwise survey matching survey_id will be updated
        survey_name: If survey_id is None, a new survey will be created using this name.
        input_dataset: File containing survey questions
        interactive: If True, asks for confirmation of changes before applying to survey
    """
    manager = DceSurveyManager(
        survey_id=survey_id,
        survey_name=survey_name,
        input_dataset=input_dataset,
    )
    manager.parse_input_csv()
    update_successful = True
    results = manager.update_survey(interactive=interactive)
    for entity in results:
        if entity:
            for verb in entity:
                if verb:
                    for _, v in verb.items():
                        try:
                            if v["meta"]["httpStatus"] != "200 - OK":
                                update_successful = False
                        except KeyError:  # add_block responses have a different structure
                            if v["create_response"]["meta"]["httpStatus"] != "200 - OK":
                                update_successful = False
                            if v["update_response"]["meta"]["httpStatus"] != "200 - OK":
                                update_successful = False
                        except TypeError:
                            logger.error("v is None", extra={"entity": entity})

    warning_message = ""
    if warning_counter:
        warning_message = (
            f" ({warning_counter} warnings were issued; see log for details)"
        )

    if update_successful:
        print(f"Survey updated successfully{warning_message}")
    else:
        print(f"Survey update failed{warning_message}")


if __name__ == "__main__":
    """
    Pass either survey_id to update an existing survey or survey_name to create a new survey.
    If survey_name == "Test survey", the survey created will be named "Test survey XXXXX", where
    XXXXX is a random 5 digit integer.
    """
    main(
        survey_name="Test survey",
    )
