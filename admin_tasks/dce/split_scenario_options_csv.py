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

import csv

OUTPUT_FILE = "SP1_health_care_options.csv"
OUTPUT_HEADER = [
    "Block",
    "Scenario",
    "Option",
    "UID",
    "Choice situation",
    "Who will pay",
    "Any difference by income",
    "Any difference by age",
    "Who gets the benefit",
    "Who receives and controls the fund",
]


def main():
    with open(OUTPUT_FILE, "w") as out:
        writer = csv.writer(out)
        writer.writerow(OUTPUT_HEADER)
        with open("SP1_health_care.csv") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == "Block":  # skip header
                    continue
                writer.writerow(
                    [
                        *row[:2],
                        "A",
                        *row[2:9],
                    ]
                )
                writer.writerow(
                    [
                        *row[:2],
                        "B",
                        *row[2:4],
                        *row[9:],
                    ]
                )


if __name__ == "__main__":
    main()
