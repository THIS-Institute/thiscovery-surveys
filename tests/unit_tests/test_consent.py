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
import copy
import json
from http import HTTPStatus
from pprint import pprint

import thiscovery_lib.utilities as utils
import src.endpoints as ep
import thiscovery_dev_tools.testing_tools as test_utils
from src.consent import Consent, ConsentEvent
from src.common.constants import CONSENT_ROWS_IN_TEMPLATE, DEFAULT_CONSENT_EMAIL_TEMPLATE


class ConsentEventTestCase(test_utils.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_consent_event = {
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
        cls.ce = ConsentEvent(cls.test_consent_event)
        cls.expected_consent_dict = {
            'anon_project_specific_user_id': 'cc694281-91a1-4bad-b46f-9b69e71503bb',
            'anon_user_task_id': '3dfa1080-9b00-401a-a620-30273046b29e',
            'consent_datetime': '2020-11-17 10:39:58+00:00',
            'consent_statements': [
                {
                    'I can confirm that I have read the information sheet dated October 23rd, 2020 (Version 3.1) for the above study. '
                    'I have had the opportunity to consider the information, ask questions, and have had these satisfactorily answered.': 'Yes'
                },
                {
                    'I understand that my participation is voluntary and that I am free to withdraw at any time without giving any reason. '
                    'I understand that my personal data will only be removed from the study records, if it is practical to do so at the '
                    'point in time that I contact the researchers.': 'No'
                },
                {
                    "I understand that my data may be accessed by the research sponsor (the Cambridge University Hospitals NHS Foundation "
                    "Trust and the University of Cambridge), or the Hospital's Research and Development Office for the purpose of monitoring "
                    "and audit only.": 'Yes'
                },
                {
                    'I agree to my interview being digitally recorded.': 'No'
                },
                {
                    'I agree to take part in the above study.': 'Yes'
                },
                {
                    'I agree that anonymised quotations from my interview may be used in reports and publications arising from the study.': 'Yes'
                },
                {
                    'I agree to be contacted at the end of the study to be invited to a workshop. '
                    'At this workshop we will focus on the practical, ethical and legal challenges of differential diagnosis '
                    'and the potential for reform.': 'No'
                },
                {
                    'I wish to be contacted at the end of the study to be informed of the findings of the study.': 'Yes'
                },
                {
                    'I understand that the information collected about me may be used to support other research in the future, '
                    'and may be shared anonymously with other researchers.': 'No'
                }],
            'project_id': None,
            'project_short_name': None,
            'project_task_id': None,
        }

    def test_01_init_ok_default_template(self):
        consent_dict = self.ce.consent.as_dict()
        self.uuid_test_and_remove(
            entity_dict=consent_dict,
            uuid_attribute_name='consent_id')
        self.assertDictEqual(self.expected_consent_dict, consent_dict)
        self.assertEqual(DEFAULT_CONSENT_EMAIL_TEMPLATE, self.ce.template_name)

    def test_02_init_ok_custom_template(self):
        custom_template = 'project_specific_participant_consent'
        event = copy.copy(self.test_consent_event)
        event['body'] = f'{event["body"].rstrip("}")}, "template_name": "{custom_template}"' + '}'
        ce = ConsentEvent(event)
        self.assertEqual(custom_template, ce.template_name)

    def test_03_init_ok_missing_consent_datetime(self):
        event = copy.copy(self.test_consent_event)
        event['body'] = event['body'].replace("\"consent_datetime\":\"2020-11-17T10:39:58+00:00\",", "")
        ce = ConsentEvent(event)
        self.now_datetime_test_and_remove(
            entity_dict=ce.consent.as_dict(),
            datetime_attribute_name='consent_datetime',
        )

    def test_04_format_consent_statements_ok(self):
        expected_consent_rows_dict = {
            'consent_row_01': 'I can confirm that I have read the information sheet dated '
                              'October 23rd, 2020 (Version 3.1) for the above study. I '
                              'have had the opportunity to consider the information, ask '
                              'questions, and have had these satisfactorily answered.',
            'consent_row_02': 'I understand that my participation is voluntary and that I '
                              'am free to withdraw at any time without giving any reason. '
                              'I understand that my personal data will only be removed '
                              'from the study records, if it is practical to do so at the '
                              'point in time that I contact the researchers.',
            'consent_row_03': 'I understand that my data may be accessed by the research '
                              'sponsor (the Cambridge University Hospitals NHS Foundation '
                              "Trust and the University of Cambridge), or the Hospital's "
                              'Research and Development Office for the purpose of '
                              'monitoring and audit only.',
            'consent_row_04': 'I agree to my interview being digitally recorded.',
            'consent_row_05': 'I agree to take part in the above study.',
            'consent_row_06': 'I agree that anonymised quotations from my interview may '
                              'be used in reports and publications arising from the '
                              'study.',
            'consent_row_07': 'I agree to be contacted at the end of the study to be '
                              'invited to a workshop. At this workshop we will focus on '
                              'the practical, ethical and legal challenges of '
                              'differential diagnosis and the potential for reform.',
            'consent_row_08': 'I wish to be contacted at the end of the study to be '
                              'informed of the findings of the study.',
            'consent_row_09': 'I understand that the information collected about me may '
                              'be used to support other research in the future, and may '
                              'be shared anonymously with other researchers.',
            'consent_row_10': '',
            'consent_row_11': '',
            'consent_row_12': '',
            'consent_row_13': '',
            'consent_row_14': '',
            'consent_row_15': '',
            'consent_row_16': '',
            'consent_row_17': '',
            'consent_row_18': '',
            'consent_row_19': '',
            'consent_row_20': '',
            'consent_value_01': 'Yes',
            'consent_value_02': 'No',
            'consent_value_03': 'Yes',
            'consent_value_04': 'No',
            'consent_value_05': 'Yes',
            'consent_value_06': 'Yes',
            'consent_value_07': 'No',
            'consent_value_08': 'Yes',
            'consent_value_09': 'No',
            'consent_value_10': '',
            'consent_value_11': '',
            'consent_value_12': '',
            'consent_value_13': '',
            'consent_value_14': '',
            'consent_value_15': '',
            'consent_value_16': '',
            'consent_value_17': '',
            'consent_value_18': '',
            'consent_value_19': '',
            'consent_value_20': '',
        }
        self.assertDictEqual(expected_consent_rows_dict, self.ce._format_consent_statements())

    def test_05_format_consent_statements_too_many_statements_raises_error(self):
        too_many_rows = CONSENT_ROWS_IN_TEMPLATE + 1
        ce = copy.copy(self.ce)
        original_statements = copy.deepcopy(ce.consent.consent_statements)
        ce.consent.consent_statements = [{f'statement_{x}': 'Yes'} for x in range(too_many_rows)]
        with self.assertRaises(utils.DetailedValueError) as context:
            ce._format_consent_statements()
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Number of consent statements exceeds maximum supported by template', err_msg)
        ce.consent.consent_statements = original_statements

    def test_06_ddb_dump_and_load_ok(self):
        consent_obj = copy.copy(self.ce.consent)
        consent_obj._ddb_client.delete_all(
            table_name='ConsentData',
            key_name='project_task_id',
            sort_key_name='consent_id',
        )
        dumped_consent_dict = copy.deepcopy(consent_obj.as_dict())
        # project_task_id, project_id and project_short_name are added during dump, so remove them from dicts being compared
        del dumped_consent_dict['project_task_id']
        del dumped_consent_dict['project_id']
        del dumped_consent_dict['project_short_name']
        self.assertEqual(HTTPStatus.OK, consent_obj.ddb_dump())
        self.assertEqual(HTTPStatus.OK, consent_obj.ddb_load())
        loaded_consent_dict = copy.deepcopy(consent_obj.as_dict())
        self.uuid_test_and_remove(entity_dict=loaded_consent_dict, uuid_attribute_name='project_task_id')
        self.uuid_test_and_remove(entity_dict=loaded_consent_dict, uuid_attribute_name='project_id')
        del loaded_consent_dict['project_short_name']
        self.assertDictEqual(dumped_consent_dict, loaded_consent_dict)

    def test_07_ddb_load_not_found(self):
        self.ce.consent._ddb_client.delete_all(
            table_name='ConsentData',
            key_name='project_task_id',
            sort_key_name='consent_id',
        )
        with self.assertRaises(utils.ObjectDoesNotExistError) as context:
            self.ce.consent.ddb_load()
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('could not be found in Dynamodb', err_msg)

    def test_08_notify_participant(self):
        result = self.ce._notify_participant()
        self.assertEqual(HTTPStatus.NO_CONTENT, result['statusCode'])

    def test_09_parse_ok(self):
        dump_result, notification_result = self.ce.parse()
        self.assertEqual(HTTPStatus.OK, dump_result)
        self.assertEqual(HTTPStatus.NO_CONTENT, notification_result)

    def test_10_send_consent_email_api_ok(self):
        test_call_body = self.test_consent_event['body']
        result = test_utils.test_post(
            local_method=ep.send_consent_email_api,
            aws_url='v1/send-consent-email',
            request_body=test_call_body,
        )
        self.assertEqual((HTTPStatus.OK, HTTPStatus.NO_CONTENT), result)
