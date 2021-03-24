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
        self.dist_client = qualtrics.DistributionsClient()
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb(stack_name=const.STACK_NAME, correlation_id=correlation_id)

    @classmethod
    def from_eb_event(cls, event):
        event_detail = event['detail']
        try:
            return cls(
                account=event_detail['account'],
                survey_id=event_detail['survey_id'],
                contact_list_id=event_detail.get('contact_list_id', const.DEFAULT_DISTRIBUTION_LIST),
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
        partition_key_name = 'survey_id'
        for row in rows:
            item = {
                partition_key_name: f'{self.account}_{self.survey_id}',
                'status': 'new',
                'url': row['link']
            }
            items.append(item)
        self.ddb_client.batch_put_items(
            table_name=const.PERSONAL_LINKS_TABLE,
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
        self.correlation_id = correlation_id
        if correlation_id is None:
            self.correlation_id = utils.new_correlation_id()

        self.ddb_client = Dynamodb(
            stack_name=const.STACK_NAME,
            correlation_id=self.correlation_id
        )

    def _get_user_link(self):
        """
        Retrieves a personal link previously assigned to this user
        """
        return self.ddb_client.get_item(
            table_name=const.PERSONAL_LINKS_TABLE,
            key=self.survey_id,
            key_name='survey_id',
            sort_key={'user_id': self.user_id},
        )

    def _get_unassigned_links(self):
        """
        Retrieves existing personal links that have not yet been assigned to an user
        """
        return self.ddb_client.query(
            table_name=const.PERSONAL_LINKS_TABLE,
            IndexName='unassigned-links',
            KeyConditionExpression='survey_id = :survey_id '
                                   'AND status = :status',
            ExpressionAttributeValues={
                ':survey_id': self.survey_id,
                ':status': 'new',
            }
        )

    def get_personal_link(self):
        try:
            return self._get_user_link()['url']
        except TypeError:  # item is None; get unassigned links and assign one to user
            unassigned_links = self._get_unassigned_links()
            unassigned_links_len = len(unassigned_links)

            if not unassigned_links:  # create links synchronously
                dlg = DistributionLinksGenerator(
                    account=self.account,
                    survey_id=self.survey_id,
                    contact_list_id=const.DEFAULT_DISTRIBUTION_LIST,
                    correlation_id=self.correlation_id,
                )
                unassigned_links = dlg.generate_links_and_upload_to_dynamodb()
            elif unassigned_links_len <= const.PERSONAL_LINKS_BUFFER:   # create links asynchronously
                eb_event = eb.ThiscoveryEvent(
                    {
                        'detail-type': 'create_personal_links',
                        'detail': {
                            'account': self.account,
                            'survey_id': self.survey_id,
                        }
                    }
                )
                eb_event.put_event()

            unassigned_links.sort(key=lambda x: x['expires'])
            user_link = unassigned_links[0]['url']

            # mark as assigned in ddb
            self.ddb_client.update_item(
                table_name=const.PERSONAL_LINKS_TABLE,
                key=f'{self.account}_{self.survey_id}',
                name_value_pairs={
                    'status': 'assigned',
                },
                key_name='survey_id',
                sort_key={
                    'url': user_link
                }
            )

            return user_link


@utils.lambda_wrapper
def create_personal_links(event, context):
    """
    Creates new personal links in Qualtrics and stores them in ddb
    """
    dlg = DistributionLinksGenerator.from_eb_event(event)
    return dlg.generate_links_and_upload_to_dynamodb()


@utils.lambda_wrapper
# @utils.api_error_handler
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
        "body": json.dumps(plm.get_personal_link())
    }
