import unittest
import requests
from api_wrappers.mailchimp_wrapper import MailchimpWrapper


class ItlMailChimp:
    mc_global = MailchimpWrapper()


class MailChimpTests(unittest.TestCase):

    def test_something(self):
        ItlMailChimp.mc_global.temp()
        assert True

    def test_get_lists(self):
        lists = ItlMailChimp.mc_global.get_lists()
        assert lists[0]['name'] == 'IntelliTect Presents'
        assert lists[0]['id'] == '96c3b8bc98'
        print('-----LISTS:-------')
        for list in lists:
            print("ID: {}; NAME: {}; MEMBER COUNT: {}".format(list['id'], list['name'], list['stats']['member_count']))
        print('------------------')

    def test_get_campaigns_campaign_id(self):
        campaign = ItlMailChimp.mc_global.get_campaign(campaign_id='17c90e3ad8')
        assert 'emails_sent' in campaign
        assert 'id' in campaign
        assert 'recipients' in campaign
        assert 'report_summary' in campaign
        assert 'send_time' in campaign
        assert 'settings' in campaign

        assert campaign['id'] == '17c90e3ad8'
        assert campaign['emails_sent'] == 34
        assert campaign['send_time'] == '2015-07-06T21:47:30+00:00'
        assert campaign['settings']['subject_line'] == 'Software & Strategy Curated - First Newsletter'
        assert campaign['settings']['title'] == 'Newsletter 1'
        print('------test_get_campaigns_campaign_id-------')
        print_campaigns([campaign])

    def test_get_campaign_report(self):
        report = ItlMailChimp.mc_global.get_campaign_report(campaign_id='17c90e3ad8')
        assert report['id'] == '17c90e3ad8'
        assert report['emails_sent'] == 34
        assert report['send_time'] == '2015-07-06T21:47:30+00:00'

    def test_get_campaigns_links(self):
        campaign_id = '17c90e3ad8'
        links = ItlMailChimp.mc_global.get_campaign_links(campaign_id=campaign_id)
        assert links['campaign_id'] == campaign_id
        assert len(links['urls_clicked']) == 20
        campaign_string = '&mc_cid=17c90e3ad8&mc_eid=[UNIQID]'

        # url | total clicks | total click % | unique clicks | unique click %
        url_export = [
            ['https://medium.com/why-not/what-will-the-automated-workplace-look-like-495f9d1e87da?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 5, 20, 4, 17],
            ['http://www.testthisblog.com/2014/10/things-tester-should-say-at-daily.html?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 4, 16, 4, 17],
            ['http://intellitect.com/ideafounder-fit?utm_source=newsletter1&utm_medium=email&utm_campaign=newsletters', 4, 16, 4, 17],
            ['http://blog.samaltman.com/super-successful-companies?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 3, 12, 2, 9],
            ['http://intellitect.com/suspend-and-resume-in-visual-studio-using-tfs?utm_source=newsletter1&utm_medium=email&utm_campaign=newsletters', 3, 12, 3, 13],
            ['http://intellitect.com/code-reviews?utm_source=newsletter1&utm_medium=email&utm_campaign=newsletters', 2, 8, 2, 9],
            ['https://baremetrics.com/blog/startup-competition?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 2, 8, 2, 9],
            ['http://www.pcmag.com/article2/0,2817,2483459,00.asp?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 1, 4, 1, 4],
            ['http://www.testthisblog.com?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 0, 0, 0, 0],
            ['https://medium.com?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 0, 0, 0, 0],
            ['https://baremetrics.com?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 0, 0, 0, 0],
            ['http://intellitect.com?utm_source=newsletter1&utm_medium=email&utm_campaign=newsletters', 0, 0, 0, 0],
            ['http://blog.samaltman.com?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 0, 0, 0, 0],
            ['http://www.pcmag.com?utm_source=newsletters&utm_medium=email&utm_campaign=IntelliTect.com', 0, 0, 0, 0]
        ]

        for link in url_export:
            assert link[0]+campaign_string in links['urls_clicked']
            assert links['urls_clicked'][link[0]+campaign_string]['campaign_id'] == campaign_id
            assert links['urls_clicked'][link[0]+campaign_string]['total_clicks'] == link[1]
            percentage = links['urls_clicked'][link[0] + campaign_string]['click_percentage'] * 100
            if percentage % 1 == 0.5:
                percentage += .5 # python rounds down at .5, mailchimp rounds up
            assert round(percentage) == link[2]
            assert links['urls_clicked'][link[0]+campaign_string]['unique_clicks'] == link[3]
            percentage = links['urls_clicked'][link[0] + campaign_string]['unique_click_percentage'] * 100
            if percentage % 1 == 0.5:
                percentage += .5  # python rounds down at .5, mailchimp rounds up
            assert round(percentage) == link[4]

    def test_get_campaigns(self):
        campaigns = ItlMailChimp.mc_global.get_campaigns()
        assert len(campaigns) > 10
        print_campaigns(campaigns)
        # print("----------")
        campaigns_software_strategy = ItlMailChimp.mc_global.get_campaigns(list_id='5b4a26e23c')
        assert len(campaigns_software_strategy) > 5
        assert 'emails_sent' in campaigns_software_strategy[0]
        assert 'id' in campaigns_software_strategy[0]
        assert 'recipients' in campaigns_software_strategy[0]
        assert 'report_summary' in campaigns_software_strategy[0]
        assert 'send_time' in campaigns_software_strategy[0]
        assert 'settings' in campaigns_software_strategy[0]
        # print_campaigns(campaigns_software_strategy)
        assert True

    def test_generic_get(self):
        self.assertRaises(ValueError, ItlMailChimp.mc_global.generic_get, endpoint='temp', fields='temp', pagination_offset=20)

        self.assertRaises(requests.exceptions.HTTPError, ItlMailChimp.mc_global.generic_get, endpoint='temp123', fields='tempabc')
        assert 'fields' in ItlMailChimp.mc_global.last_params
        assert ItlMailChimp.mc_global.last_params['fields'] == 'tempabc'

        self.assertRaises(requests.exceptions.HTTPError, ItlMailChimp.mc_global.generic_get, endpoint='temp456')
        assert 'fields' not in ItlMailChimp.mc_global.last_params
        assert 'exclude_fields' not in ItlMailChimp.mc_global.last_params

        self.assertRaises(requests.exceptions.HTTPError, ItlMailChimp.mc_global.generic_get, endpoint='temp', fields='temp_fields', exclude_fields='temp_exclude',pagination_count=20)
        assert 'count' in ItlMailChimp.mc_global.last_params
        assert 'offset' in ItlMailChimp.mc_global.last_params
        assert 'fields' in ItlMailChimp.mc_global.last_params
        assert 'exclude_fields' in ItlMailChimp.mc_global.last_params

        assert ItlMailChimp.mc_global.last_params['fields'] == 'temp_fields'
        assert ItlMailChimp.mc_global.last_params['exclude_fields'] == 'temp_exclude'
        assert ItlMailChimp.mc_global.last_params['count'] == 20
        assert ItlMailChimp.mc_global.last_params['offset'] == 0

        self.assertRaises(requests.exceptions.HTTPError, ItlMailChimp.mc_global.generic_get, endpoint='temp', pagination_count=30, pagination_offset=4)
        assert 'count' in ItlMailChimp.mc_global.last_params
        assert 'offset' in ItlMailChimp.mc_global.last_params
        assert 'fields' not in ItlMailChimp.mc_global.last_params
        assert ItlMailChimp.mc_global.last_params['count'] == 30
        assert ItlMailChimp.mc_global.last_params['offset'] == 4


def print_campaigns(campaigns):
        for campaign in campaigns:
            print(
                "from: {}-{}, {}; sent: {};  sent_number: {}, list: {}; id: {}; opens: {}, unique_opens {}, clicks: {}; subscriber clicks: {}; click rate: {}".format(
                    campaign['settings']['from_name'] if 'from_name' in
                                                         campaign[
                                                             'settings'] else '-',
                    campaign['settings']['title'],
                    campaign['settings']['subject_line'] if 'subject_line' in
                                                            campaign[
                                                                'settings'] else '-',
                    campaign['send_time'],
                    campaign['emails_sent'],
                    campaign['recipients']['list_id'],
                    campaign['id'],
                    campaign['report_summary'][
                        'opens'] if 'report_summary' in campaign else '-',
                    campaign['report_summary'][
                        'unique_opens'] if 'report_summary' in campaign else '-',
                    campaign['report_summary'][
                        'clicks'] if 'report_summary' in campaign else '-',
                    campaign['report_summary'][
                        'subscriber_clicks'] if 'report_summary' in campaign else '-',
                    campaign['report_summary'][
                        'click_rate'] if 'report_summary' in campaign else '-',
                ))
            if 'variate_settings' in campaign:
                print("---AB Tested---")


if __name__ == '__main__':
    unittest.main()

