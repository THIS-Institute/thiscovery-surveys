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
STACK_NAME = 'thiscovery-surveys'
CONSENT_DATA_TABLE = 'ConsentData'
DEFAULT_CONSENT_EMAIL_TEMPLATE = 'participant_consent'
CONSENT_ROWS_IN_TEMPLATE = 20
INTERVIEW_TASKS_TABLE = {
    'name': 'InterviewTasks',
    'partition_key': 'project_task_id',
    'sort_key': 'interview_task_id',
}
TASK_RESPONSES_TABLE = {
    'name': 'TaskResponses',
    'partition_key': 'response_id',
    'sort_key': 'event_time',
}
INTERVIEW_QUESTIONS_TABLE = 'InterviewQuestions'
