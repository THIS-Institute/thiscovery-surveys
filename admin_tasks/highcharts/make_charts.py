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
import os
import pandas as pd

from highcharts import Highchart

THISCOVERY_RED = "#DD0031"
AXIS_TITLE_CSS = {"font-weight": "bold"}
Y_AXIS_TITLE = "Number of GP responses"
X_AXIS_CATEGORIES = [1, 2, 3, 4, 5, 6, 7, 8, 9]
BAR_CHART_OPTIONS = {
    "chart": {
        "style": {
            "fontFamily": "'Brown-Regular', Arial, 'Helvetica Neue', Helvetica, sans-serif"
        }
    },
    "credits": {
        "enabled": True,
        "href": None,
        "text": "Thiscovery",
        "style": {"color": THISCOVERY_RED},
    },
    "exporting": {"enabled": False},
    "title": {"text": None},
    # "subtitle": {"text": "According to the Standard Atmosphere Model"},
    "xAxis": [
        {
            "reversed": False,
            "categories": X_AXIS_CATEGORIES,
            # "labels": {
            #     "formatter": "function () {\
            #         return this.value;\
            #     }"
            # },
            "maxPadding": 0.05,
            "showLastLabel": True,
        },
        {
            "categories": [
                "not important at all",
                "",
                "",
                "",
                "neutral",
                "",
                "",
                "",
                "extremely important",
            ],
            "labels": {
                "autoRotation": None,
                # "formatter": "function () {\
                #     return this.value;\
                # }"
                "overflow": "allow",
            },
            "lineWidth": 0,
            "linkedTo": 0,
            "minorTickLength": 0,
            "opposite": False,
            "tickLength": 0,
            "title": {
                "enabled": True,
                "margin": 20,
                "text": "Rating",
                "style": AXIS_TITLE_CSS,
            },
        },
    ],
    "yAxis": {
        "allowDecimals": False,
        "title": {"text": Y_AXIS_TITLE, "style": AXIS_TITLE_CSS},
        # "labels": {
        #     "formatter": "function () {\
        #             return this.value;\
        #         }"
        # },
        "lineWidth": 0,
    },
    "legend": {"enabled": False},
    "tooltip": {
        "headerFormat": None,
        "pointFormat": "<b>{point.y}</b><br/>",
    },
}


def get_data_from_excel_file(filename):
    return pd.read_excel(filename)


def plot_bar_chart_from_pandas_dataframe(df):
    assert list(df[df.columns[0]]) == list(
        range(1, len(X_AXIS_CATEGORIES) + 1)
    ), "Dataframe categories are in the wrong order"
    assert len(df.index) == len(
        X_AXIS_CATEGORIES
    ), "Dataframe does not contain values for every category"
    question_export_tag = df.columns[0]
    chart = Highchart()
    chart.set_dict_options(BAR_CHART_OPTIONS)
    for series_name in df.columns[1:]:
        data = list(df[series_name])
        chart.add_data_set(
            data,
            series_type="bar",
            name=series_name,
            color=THISCOVERY_RED,  # todo: create a colour generator to yield each series colour
        )
    chart.save_file(filename=question_export_tag)


def main(input_folder=None):
    if input_folder is None:
        input_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "chartdata"
        )
    input_files = [os.path.join(input_folder, x) for x in os.listdir(input_folder)]
    for f in input_files:
        df = get_data_from_excel_file(filename=f)
        plot_bar_chart_from_pandas_dataframe(df=df)


if __name__ == "__main__":
    main()
