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
import pandas as pd

from pprint import pprint
from thiscovery_dev_tools.scripting_tools import CsvImporter


class GraphDataGenerator(CsvImporter):
    def __init__(
        self,
        study_group_column_heading,
        study_groups_definition,
        target_questions,
        target_levels,
        input_filename=None,
    ):
        if input_filename:
            self.input_filename = input_filename
        else:
            super().__init__()
        self.df = pd.read_csv(self.input_filename)
        self.target_questions = target_questions
        self.target_levels = target_levels
        self.study_groups_definition = study_groups_definition

        # Delete redundant row (column labels) from Qualtrics results
        if self.df.at[0, "StartDate"] == "Start Date":
            self.df.drop(index=0, inplace=True)

        # group dataframe by study groups
        replacement_mapping = dict()
        for k, groups in study_groups_definition.items():
            for g in groups:
                replacement_mapping[g] = k
        self.df[study_group_column_heading] = self.df[study_group_column_heading].map(
            replacement_mapping
        )
        self.groups = self.df.groupby(study_group_column_heading)

    def export_graph_data(self):
        for q in self.target_questions:
            q_df = self.groups[q].value_counts(sort=False).unstack(0)
            q_df.fillna(0)  # replace NaN with zeroes

            # ensure all target levels are represented
            q_levels = list(q_df.index)
            for level in self.target_levels:
                if level not in q_levels:
                    new_row = pd.Series(
                        {
                            x: 0 for x in self.study_groups_definition.keys()
                        },  # add 0 observations of level for each study group
                        name=level,
                    )
                    q_df = q_df.append(new_row)

            q_df.sort_index(inplace=True)  # sort df levels
            q_df.to_csv(f"{q.replace('.','-')}.csv")


def main(
    study_group_column_heading: str,
    study_groups_definition: dict[str, list],
    target_questions: list,
    target_levels: list,
    input_filename: str,
):
    gdg = GraphDataGenerator(
        study_group_column_heading,
        study_groups_definition,
        target_questions,
        target_levels,
        input_filename,
    )
    gdg.export_graph_data()


if __name__ == "__main__":
    main(
        study_group_column_heading="Q3.1",
        study_groups_definition={
            "Patients/carers": [
                "Patient",
                "Carer",
            ],
            "Healthcare professionals": [
                "Healthcare provider",
                "Other healthcare professional",
            ],
        },
        target_questions=[
            "Q7.4_1",
            "Q7.4_2",
            "Q7.4_3",
            "Q7.4_5",
            "Q7.4_7",
            "Q8.3_11",
            "Q9.1_3",
            "Q10.1_5",
            "Q10.1_6",
            "Q10.1_8",
            "Q10.1_10",
            "Q10.2_3",
            "Q10.2_4",
            "Q10.2_5",
            "Q10.2_6",
            "Q10.2_7",
            "Q11.1_5",
            "Q11.1_6",
            "Q11.1_7",
            "Q11.1_9",
            "Q11.2_1",
            "Q11.2_3",
            "Q11.2_5",
            "Q11.2_6",
            "Q12.1_3",
            "Q12.1_5",
            "Q13.1_5",
            "Q14.1_1",
            "Q14.2_2",
            "Q14.2_5",
        ],
        target_levels=[str(x) for x in range(1, 9)],
        input_filename="HFpEF_pandas.csv",
    )
