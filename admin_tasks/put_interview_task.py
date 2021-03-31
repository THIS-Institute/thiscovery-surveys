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
import local.dev_config  # sets env variables TEST_ON_AWS and AWS_TEST_API
import local.secrets  # sets env variables THISCOVERY_AFS25_PROFILE and THISCOVERY_AMP205_PROFILE
import thiscovery_lib.utilities as utils
import uuid
from src.interview_tasks import InterviewTask


def main(task_dict, task_id=None):
    if task_id is None:
        task_id = str(uuid.uuid4())
    project_task_id = task_dict["project_task_id"]
    interview_task = InterviewTask(project_task_id, task_id)
    interview_task.from_dict(item_dict=task_dict)
    interview_task.ddb_dump()
    return task_id


if __name__ == "__main__":
    interview_task_dict = {
        "project_task_id": "TBC",
        "name": "TBC",
        "short_name": "TBC",
        "description": "TBC",
        "completion_url": "TBC",
        "on_demand_available": False,
        "on_demand_survey_id": "TBC",
        "live_available": True,
        "live_survey_id": "TBC",
        "appointment_type_id": "TBC",
        "modified": utils.now_with_tz(),
    }
    new_task_id = main(
        task_dict=interview_task_dict,
    )
    print(f"ID of new interview task: {new_task_id}")
