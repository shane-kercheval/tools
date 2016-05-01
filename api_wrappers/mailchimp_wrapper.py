import os
import requests
import json
import urllib.parse


class MailChimpConfig:


    def __init__(self, credentials_json=None, api_key=None):
        if credentials_json is None and api_key is None:
            raise ValueError("must pass credentials (json) file or api_key")

        if api_key is not None:
            self.api_key, self.shard, self.api_root = MailChimpConfig.get_api_values(api_key)

        else:
            if os.path.isfile(credentials_json) is False:
                raise SyntaxError("credentials file not found")

            with open(credentials_json) as json_file:
                json_data = json.load(json_file)
                assert 'mailchimp' in json_data
                assert 'api_key' in json_data['mailchimp']
                api_key = json_data['mailchimp']['api_key']
                self.api_key, self.shard, self.api_root = MailChimpConfig.get_api_values(api_key)

    @staticmethod
    def get_api_values(api_key):
        parts = api_key.split('-')
        if len(parts) != 2:
            raise SyntaxError("This doesn't look like an API Key: " + api_key)

        return api_key, parts[1], "https://" + parts[
            1] + ".api.mailchimp.com/3.0/"


class MailchimpWrapper:

    def get_lists(self):
        json = self.generic_get(endpoint='lists', fields='lists.id,lists.name,lists.stats.member_count')
        return json['lists']

    def get_campaigns(self, list_id=None, pagination_count=None):
        json = self.generic_get('campaigns',
                                fields=MailchimpWrapper.get_campaign_fields(False),
                                pagination_count=pagination_count or 30)
        if list_id is None:
            return json['campaigns']
        else:
            list = [campaign for campaign in json['campaigns'] if campaign['recipients']['list_id'] == list_id]
            return list

    def get_campaign(self, campaign_id):
        json = self.generic_get("campaigns/{}/".format(campaign_id),
                                fields=MailchimpWrapper.get_campaign_fields(True))
        return json

    def get_campaign_report(self, campaign_id):
        json = self.generic_get("reports/{}/".format(campaign_id))
        return json

    def get_campaign_links(self, campaign_id):
        exclude_fields = 'urls_clicked._links,urls_clicked.last_click'
        json = self.generic_get("reports/{}/click-details/"
                                .format(campaign_id),
                                exclude_fields=exclude_fields,
                                pagination_count=100)
        results = {'campaign_id': json['campaign_id'], 'urls_clicked': {}}
        for link in json['urls_clicked']:
            if link['url'] in results['urls_clicked']:
                results['urls_clicked'][link['url']]['click_percentage'] += link['click_percentage']
                results['urls_clicked'][link['url']]['total_clicks'] += link['total_clicks']
                results['urls_clicked'][link['url']]['unique_click_percentage'] += link['unique_click_percentage']
                results['urls_clicked'][link['url']]['unique_clicks'] += link['unique_clicks']
            else:
                results['urls_clicked'][link['url']] = link

        return results

    @staticmethod
    def get_campaign_fields(is_single_campaign):
        return '{0}id,{0}emails_sent,{0}send_time,{0}recipients.list_id,{0}settings.title,{0}settings.from_name,{0}settings.subject_line,{0}report_summary,{0}variate_settings'.format('' if is_single_campaign else "campaigns.")

    def generic_get(self, endpoint, fields=None, exclude_fields=None, pagination_count=None, pagination_offset=None):
        endpoint = urllib.parse.urljoin(self.config.api_root, endpoint)
        params = {}
        if fields is not None:
            params['fields'] = fields

        if exclude_fields is not None:
            params['exclude_fields'] = exclude_fields

        if pagination_count is not None:
            pagination_offset = pagination_offset or 0
            params['count'] = pagination_count
            params['offset'] = pagination_offset
        elif pagination_offset is not None:
            raise ValueError("pagination_offset set to {}, but pagination_count not set".format(pagination_offset))

        self.last_params = params # used for testing and so client can get params used
        response = requests.get(endpoint,
                                auth=('apikey', self.config.api_key),
                                params=params,
                                verify=False)

        response.raise_for_status()
        return response.json()

    def __init__(self, credentials_json=None, api_key=None):
        self.config = MailChimpConfig(credentials_json=credentials_json, api_key=api_key)

    def temp(self):

        endpoint = self.config.api_root

        response = requests.get(endpoint, auth=('apikey', self.config.api_key))
        print(response.url)

        try:
          response.raise_for_status()
          response_json = response.json()
        except requests.exceptions.HTTPError as err:
          print('Error: %s' % err)
        except ValueError:
          print("Cannot decode JSON, got %s" % response.text)

        print("Headers:")
        for header in response.headers:
            print('\t'.join(['',header.ljust(20), response.headers[header]]))

        print("\nJSON:")
        print(json.dumps(response_json, indent=4))

