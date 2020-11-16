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
import unittest
from http import HTTPStatus
from pprint import pprint

import thiscovery_lib.utilities as utils
import src.endpoints as ep
import thiscovery_dev_tools.testing_tools as test_utils
from src.consent import Consent, ConsentEvent


class ConsentEventTestCase(test_utils.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_consent_event_json = {
            "resource": "/v1/send-consent-email",
            "path": "/v1/send-consent-email",
            "httpMethod": "POST",
            "logger": utils.get_logger(),
            "correlation_id": "d3ef676b-8dc4-424b-9250-475f8340f1a4",
            "body": "{\"template_name\":\"participant_consent\","
                    "\"current_date\":\"16 Nov 2020\","
                    "\"current_time\":\"10:57 PM\","
                    "\"user_first_name\":\"Fred\","
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
                    "\"to_recipient_id\":\"\","
                    "\"consent_info_url\":\"https://preview.hs-sites.com/_hcms/preview/content/37340326054?portalId=4783957&_preview=true&cacheBust=0"
                    "&preview_key=SepYNCoB&from_buffer=false\""
                    "}"
        }

    def test_01_init_ok(self):
        ce = ConsentEvent(self.test_consent_event_json)
        pprint(ce.consent.as_dict())
