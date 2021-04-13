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
import os
import thiscovery_lib.utilities as utils

BASE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

QUALTRICS_TEST_OBJECTS = {
    "unittest-contact-list-1": {
        "id": "ML_6ifLPwSfjagoQ3H",
    },
    "unittest-survey-1": {
        "id": "SV_2avH1JdVZa8eEAd",
        "export_tags": [
            "StartDate",
            "EndDate",
            "Status",
            "IPAddress",
            "Progress",
            "Duration (in seconds)",
            "Finished",
            "RecordedDate",
            "LocationLatitude",
            "LocationLongitude",
            "DistributionChannel",
            "UserLanguage",
            "Q12_1",
            "Q12_2",
            "Q12_3",
            "Q12_4",
            "Q12_5",
            "Q12_6",
            "Q12_7",
            "Q12_8",
            "Q1",
            "Q1COM",
            "Q2",
            "Q2COM",
            "Q3",
            "Q12",
            "Q12_8_TEXT",
            "Q14",
            "Q14_12_TEXT",
            "Q12_DO",
            "Q1_DO",
            "Q2_DO",
            "Q3_DO",
            "Q4_DO",
            "Q14_DO",
            "Q1COM_DO",
            "Q4COM_DO",
            "RecipientEmail",
            "Q3COM",
            "Q2COM_DO",
            "RecipientLastName",
            "RecipientFirstName",
            "ExternalReference",
            "Q4",
            "Q4COM",
            "Q3COM_DO",
        ],
        "response_1_id": "R_1BziZVeffoDpTQl",
        "response_2_id": "R_0d1ampzLtZpZRjX",
    },
}

ARBITRARY_UUID = "e2e144e7-276e-4fbe-a72e-0e11a1389047"

TEST_RESPONSE_DICT = {
    "survey_id": QUALTRICS_TEST_OBJECTS["unittest-survey-1"]["id"],
    "response_id": QUALTRICS_TEST_OBJECTS["unittest-survey-1"]["response_2_id"],
    "project_task_id": "f60d5204-57c1-437f-a085-1943ad9d174f",  # PSFU-04-A
    "anon_project_specific_user_id": ARBITRARY_UUID,
    "anon_user_task_id": ARBITRARY_UUID,
}

TEST_CONSENT_EVENT = {
    "resource": "/v1/send-consent-email",
    "path": "/v1/send-consent-email",
    "httpMethod": "POST",
    "logger": utils.get_logger(),
    "correlation_id": "d3ef676b-8dc4-424b-9250-475f8340f1a4",
    "body": '{"consent_datetime":"2020-11-17T10:39:58+00:00",'
    '"first_name":"Glenda",'
    '"consent_statements":"['
    '{\\"I can confirm that I have read the information '
    "sheet dated October 23rd, 2020 (Version 3.1) for the above study. "
    "I have had the opportunity to consider the information, ask questions, "
    'and have had these satisfactorily answered.\\":\\"Yes\\"},'
    '{\\"I understand that my participation is voluntary and that I am free '
    "to withdraw at any time without giving any reason. I understand that my "
    "personal data will only be removed from the study records, if it is practical"
    ' to do so at the point in time that I contact the researchers.\\":\\"No\\"},'
    '{\\"I understand that my data may be accessed by the research sponsor '
    "(the Cambridge University Hospitals NHS Foundation Trust and the University "
    "of Cambridge), or the Hospital's Research and Development Office for the purpose"
    ' of monitoring and audit only.\\":\\"Yes\\"},'
    '{\\"I agree to my interview being digitally recorded.\\":\\"No\\"},'
    '{\\"I agree to take part in the above study.\\":\\"Yes\\"},'
    '{\\"I agree that anonymised quotations from my interview may be used in reports '
    'and publications arising from the study.\\":\\"Yes\\"},'
    '{\\"I agree to be contacted at the end of the study to be invited to a workshop. '
    "At this workshop we will focus on the practical, ethical and legal challenges "
    'of differential diagnosis and the potential for reform.\\":\\"No\\"},'
    '{\\"I wish to be contacted at the end of the study to be informed of '
    'the findings of the study.\\":\\"Yes\\"},'
    '{\\"I understand that the information collected about me may be used to '
    "support other research in the future, and may be shared anonymously with "
    'other researchers.\\":\\"No\\"}'
    ']",'
    '"anon_project_specific_user_id":"cc694281-91a1-4bad-b46f-9b69e71503bb",'
    '"anon_user_task_id":"3dfa1080-9b00-401a-a620-30273046b29e",'
    '"consent_info_url":"https://preview.hs-sites.com/_hcms/preview/content/37340326054?portalId=4783957&_preview=true&cacheBust=0'
    '&preview_key=SepYNCoB&from_buffer=false"'
    "}",
}

TEST_INTERVIEW_TASK = {
    "interview_task_id": "0fda6eff-b1e5-44df-93b4-3d71c03adeff",
    "project_task_id": "b335c46a-bc1b-4f3d-ad0f-0b8d0826a908",
    "name": "PSFU-06-A interview for healthcare professionals",
    "short_name": "PSFU-06-A hcp interview",
    "description": "Questions about PSFU-06-A",
    "completion_url": "https://www.thiscovery.org/",
    "on_demand_available": False,
    "on_demand_survey_id": None,
    "live_available": True,
    "live_survey_id": "SV_eDrjXPqGElN0Mwm",
    "appointment_type_id": "448161419",
}

TEST_USER_INTERVIEW_TASK = {
    "response_id": "SV_b8jGMAQJjUfsIVU-R_27PS3xFkIH36j29",
    "event_time": "2021-02-15 21:57:43.598087",
    "anon_project_specific_user_id": "7e6e4bca-4f0b-4f71-8660-790c1baf3b11",
    "anon_user_task_id": "2035dce9-9745-46cc-8db0-3e8de47c463b",
    "interview_task_id": "0fda6eff-b1e5-44df-93b4-3d71c03adeff",
    "detail_type": "user_interview_task",
}

TEST_USER_INTERVIEW_TASK_EB_EVENT = {
    "version": "0",
    "id": "b87770f0-e681-09df-afb9-970d4ac08468",
    "detail-type": "user_interview_task",
    "detail": {
        "anon_project_specific_user_id": TEST_USER_INTERVIEW_TASK[
            "anon_project_specific_user_id"
        ],
        "anon_user_task_id": TEST_USER_INTERVIEW_TASK["anon_user_task_id"],
        "interview_task_id": TEST_USER_INTERVIEW_TASK["interview_task_id"],
        "response_id": TEST_USER_INTERVIEW_TASK["response_id"],
    },
    "source": "qualtrics",
    "account": "REDACTED",
    "region": "REDACTED",
    "resources": [],
    "time": "2021-02-12T10:57:09Z",
}

TEST_INTERVIEW_QUESTIONS_UPDATED_EB_EVENT = {
    "version": "0",
    "id": "ead25aa5-a106-1bf6-7d5f-ab2ea0c7d89e",
    "detail-type": "interview_questions_update",
    "source": "qualtrics",
    "account": "REDACTED",
    "time": "2021-02-16T14:34:57Z",
    "region": "REDACTED",
    "resources": [],
    "detail": {"account": "cambridge", "survey_id": "SV_eDrjXPqGElN0Mwm"},
}

TEST_INTERVIEW_QUESTIONS_UPDATED_ON_THIS_ACCOUNT_EB_EVENT = {
    "version": "0",
    "id": "58ceb8da-5fe0-f913-4588-285ccb704d74",
    "detail-type": "interview_questions_update",
    "source": "qualtrics",
    "account": "REDACTED",
    "time": "2021-02-16T16:00:52Z",
    "region": "REDACTED",
    "resources": [],
    "detail": {"account": "thisinstitute", "survey_id": "SV_es3NB93TQnNOWgu"},
}

TEST_SURVEY_USER_AGENT_EB_EVENT = {
    "account": "REDACTED",
    "detail": {
        "anon_project_specific_user_id": TEST_USER_INTERVIEW_TASK[
            "anon_project_specific_user_id"
        ],
        "anon_user_task_id": TEST_USER_INTERVIEW_TASK["anon_user_task_id"],
        "browser_type": "Firefox",
        "browser_version": "86.0",
        "os": "Ubuntu",
        "response_id": TEST_USER_INTERVIEW_TASK["response_id"],
        "screen_resolution": "1280x1024",
        "user_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
    },
    "detail-type": "survey_user_agent",
    "id": "08a9d16b-b5db-1061-b111-d5b630b16cc9",
    "region": "REDACTED",
    "resources": [],
    "source": "qualtrics",
    "time": "2021-03-02T21:46:18Z",
    "version": "0",
}
