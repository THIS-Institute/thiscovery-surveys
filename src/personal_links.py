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
import json
import thiscovery_lib.eb_utilities as eb
import thiscovery_lib.qualtrics as qualtrics
import thiscovery_lib.utilities as utils

from http import HTTPStatus
from thiscovery_lib.dynamodb_utilities import Dynamodb

import common.constants as const


class DistributionLinksGenerator:

    def __init__(self, account, survey_id, contact_list_id, correlation_id=None):
        self.account = account
        self.survey_id = survey_id
        self.contact_list_id = contact_list_id
        self.dist_client = qualtrics.DistributionsClient(qualtrics_account_name=account)
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb(stack_name=const.STACK_NAME, correlation_id=correlation_id)

    @classmethod
    def from_eb_event(cls, event):
        event_detail = event['detail']
        try:
            account = event_detail['account']
            return cls(
                account=account,
                survey_id=event_detail['survey_id'],
                contact_list_id=event_detail.get('contact_list_id', const.DISTRIBUTION_LISTS[account]['id']),
                correlation_id=event['id'],
            )
        except KeyError as exc:
            raise utils.DetailedValueError(
                f'Mandatory {exc} data not found in source event',
                details={
                    'event': event,
                }
            )

    def generate_links_and_upload_to_dynamodb(self):
        r = self.dist_client.create_individual_links(survey_id=self.survey_id, contact_list_id=self.contact_list_id)
        distribution_id = r['result']['id']
        r = self.dist_client.list_distribution_links(distribution_id, self.survey_id)
        rows = r['result']['elements']
        items = list()
        partition_key_name = const.PersonalLinksTable.PARTITION
        for row in rows:
            item = {
                partition_key_name: f'{self.account}_{self.survey_id}',
                'status': 'new',
                'url': row.pop('link'),
                'expires': row.pop('linkExpiration'),
                'details': row,
            }
            items.append(item)
        self.ddb_client.batch_put_items(
            table_name=const.PersonalLinksTable.NAME,
            items=items,
            partition_key_name=partition_key_name,
            item_type='personal survey link',
        )
        return items


class PersonalLinkManager:

    def __init__(self, survey_id, user_id, account, correlation_id=None):
        self.survey_id = survey_id
        self.user_id = user_id
        self.account = account
        self.account_survey_id = f'{account}_{survey_id}'
        self.correlation_id = correlation_id
        if correlation_id is None:
            self.correlation_id = utils.new_correlation_id()

        self.ddb_client = Dynamodb(
            stack_name=const.STACK_NAME,
            correlation_id=self.correlation_id
        )

    def _query_user_link(self) -> list:
        """
        Retrieves a personal link previously assigned to this user
        """
        return self.ddb_client.query(
            table_name=const.PersonalLinksTable.NAME,
            IndexName='assigned-links',
            KeyConditionExpression='user_id = :user_id '
                                   'AND account_survey_id = :account_survey_id',
            ExpressionAttributeValues={
                ':user_id': self.user_id,
                ':account_survey_id': self.account_survey_id,
            },
        )

    def _get_unassigned_links(self):
        """
        Retrieves existing personal links that have not yet been assigned to an user
        """
        return self.ddb_client.query(
            table_name=const.PersonalLinksTable.NAME,
            IndexName='unassigned-links',
            KeyConditionExpression='account_survey_id = :account_survey_id '
                                   'AND #status = :link_status',
            ExpressionAttributeValues={
                ':account_survey_id': self.account_survey_id,
                ':link_status': 'new',
            },
            ExpressionAttributeNames={'#status': 'status'},  # needed because status is a reserved word in ddb
        )

    def _assign_link_to_user(self, link):
        self.ddb_client.update_item(
            table_name=const.PersonalLinksTable.NAME,
            key=self.account_survey_id,
            name_value_pairs={
                'status': 'assigned',
                'user_id': self.user_id,
            },
            key_name='account_survey_id',
            sort_key={'url': link},
        )

    def _put_create_personal_links_event(self):
        eb_event = eb.ThiscoveryEvent(
            {
                'detail-type': 'create_personal_links',
                'detail': {
                    'account': self.account,
                    'survey_id': self.survey_id,
                }
            }
        )
        return eb_event.put_event()

    def _create_personal_links(self):
        dlg = DistributionLinksGenerator(
            account=self.account,
            survey_id=self.survey_id,
            contact_list_id=const.DISTRIBUTION_LISTS[self.account]['id'],
            correlation_id=self.correlation_id,
        )
        return dlg.generate_links_and_upload_to_dynamodb()

    def get_personal_link(self):
        try:
            return self._query_user_link()[0]['url']
        except IndexError:  # user link not found; get unassigned links and assign one to user
            unassigned_links = self._get_unassigned_links()
            unassigned_links_len = len(unassigned_links)
            if not unassigned_links:  # unassigned links not found; create some synchronously
                unassigned_links = self._create_personal_links()
            elif unassigned_links_len < const.PersonalLinksTable.BUFFER:   # create links asynchronously
                self._put_create_personal_links_event()

            # assign oldest link to user
            unassigned_links.sort(key=lambda x: x['expires'])
            user_link = unassigned_links[0]['url']
            self._assign_link_to_user(user_link)

            return user_link


@utils.lambda_wrapper
def create_personal_links(event, context):
    """
    Creates new personal links in Qualtrics and stores them in ddb
    """
    dlg = DistributionLinksGenerator.from_eb_event(event)
    return dlg.generate_links_and_upload_to_dynamodb()


@utils.lambda_wrapper
@utils.api_error_handler
def get_personal_link_api(event, context):
    valid_accounts = ['cambridge', 'thisinstitute']
    logger = event['logger']
    correlation_id = event['correlation_id']
    params = event['queryStringParameters']

    # validate params
    try:
        survey_id = params['survey_id']
        user_id = str(utils.validate_uuid(params['user_id']))
        if (account := params['account']) not in valid_accounts:
            raise utils.DetailedValueError(
                f'Account {account} is not supported. Valid values are {",".join(valid_accounts)}',
                details={'params': params}
            )
    except KeyError as err:
        raise utils.DetailedValueError(
                f'Mandatory {err} data not provided',
                details={'params': params}
            )

    logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'survey_id': survey_id})
    plm = PersonalLinkManager(
        survey_id=survey_id,
        user_id=user_id,
        account=account,
    )
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(
            {'personal_link': plm.get_personal_link()}
        )
    }
