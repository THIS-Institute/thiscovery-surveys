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


BASE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')

QUALTRICS_TEST_OBJECTS = {
    'unittest-contact-list-1': {
        'id': 'ML_6ifLPwSfjagoQ3H',
    },
    'unittest-survey-1': {
        'id': 'SV_2avH1JdVZa8eEAd',
        'export_tags': [
            'StartDate',
            'EndDate',
            'Status',
            'IPAddress',
            'Progress',
            'Duration (in seconds)',
            'Finished',
            'RecordedDate',
            'LocationLatitude',
            'LocationLongitude',
            'DistributionChannel',
            'UserLanguage',
            'Q12_1',
            'Q12_2',
            'Q12_3',
            'Q12_4',
            'Q12_5',
            'Q12_6',
            'Q12_7',
            'Q12_8',
            'Q1',
            'Q1COM',
            'Q2',
            'Q2COM',
            'Q3',
            'Q12',
            'Q12_8_TEXT',
            'Q14',
            'Q14_12_TEXT',
            'Q12_DO',
            'Q1_DO',
            'Q2_DO',
            'Q3_DO',
            'Q4_DO',
            'Q14_DO',
            'Q1COM_DO',
            'Q4COM_DO',
            'RecipientEmail',
            'Q3COM',
            'Q2COM_DO',
            'RecipientLastName',
            'RecipientFirstName',
            'ExternalReference',
            'Q4',
            'Q4COM',
            'Q3COM_DO',
        ],
        'response_1_id': 'R_1BziZVeffoDpTQl',
        'response_2_id': 'R_0d1ampzLtZpZRjX',
    },
}


ARBITRARY_UUID = 'e2e144e7-276e-4fbe-a72e-0e11a1389047'


TEST_RESPONSE_DICT = {
    'survey_id': QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id'],
    'response_id': QUALTRICS_TEST_OBJECTS['unittest-survey-1']['response_2_id'],
    'project_task_id': 'f60d5204-57c1-437f-a085-1943ad9d174f',  # PSFU-04-A
    'anon_project_specific_user_id': ARBITRARY_UUID,
    'anon_user_task_id': ARBITRARY_UUID,
}


TEST_CONSENT_EVENT = {
    "resource": "/v1/send-consent-email",
    "path": "/v1/send-consent-email",
    "httpMethod": "POST",
    "logger": utils.get_logger(),
    "correlation_id": "d3ef676b-8dc4-424b-9250-475f8340f1a4",
    "body": "{\"consent_datetime\":\"2020-11-17T10:39:58+00:00\","
            "\"first_name\":\"Glenda\","
            "\"consent_statements\":\"["
            "{\\\"I can confirm that I have read the information "
            "sheet dated October 23rd, 2020 (Version 3.1) for the above study. "
            "I have had the opportunity to consider the information, ask questions, "
            "and have had these satisfactorily answered.\\\":\\\"Yes\\\"},"
            "{\\\"I understand that my participation is voluntary and that I am free "
            "to withdraw at any time without giving any reason. I understand that my "
            "personal data will only be removed from the study records, if it is practical"
            " to do so at the point in time that I contact the researchers.\\\":\\\"No\\\"},"
            "{\\\"I understand that my data may be accessed by the research sponsor "
            "(the Cambridge University Hospitals NHS Foundation Trust and the University "
            "of Cambridge), or the Hospital's Research and Development Office for the purpose"
            " of monitoring and audit only.\\\":\\\"Yes\\\"},"
            "{\\\"I agree to my interview being digitally recorded.\\\":\\\"No\\\"},"
            "{\\\"I agree to take part in the above study.\\\":\\\"Yes\\\"},"
            "{\\\"I agree that anonymised quotations from my interview may be used in reports "
            "and publications arising from the study.\\\":\\\"Yes\\\"},"
            "{\\\"I agree to be contacted at the end of the study to be invited to a workshop. "
            "At this workshop we will focus on the practical, ethical and legal challenges "
            "of differential diagnosis and the potential for reform.\\\":\\\"No\\\"},"
            "{\\\"I wish to be contacted at the end of the study to be informed of "
            "the findings of the study.\\\":\\\"Yes\\\"},"
            "{\\\"I understand that the information collected about me may be used to "
            "support other research in the future, and may be shared anonymously with "
            "other researchers.\\\":\\\"No\\\"}"
            "]\","
            "\"anon_project_specific_user_id\":\"cc694281-91a1-4bad-b46f-9b69e71503bb\","
            "\"anon_user_task_id\":\"3dfa1080-9b00-401a-a620-30273046b29e\","
            "\"consent_info_url\":\"https://preview.hs-sites.com/_hcms/preview/content/37340326054?portalId=4783957&_preview=true&cacheBust=0"
            "&preview_key=SepYNCoB&from_buffer=false\""
            "}"
}
