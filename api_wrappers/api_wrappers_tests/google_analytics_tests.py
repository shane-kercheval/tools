import json
import unittest
from datetime import timedelta, datetime
from api_wrappers.google_analytics_wrapper import GoogleAnalyticsWrapper


class GAValues:
    def __init__(self):
        with open('../../../settings/credentials.json') as json_file:
            json_data = json.load(json_file)
            assert 'google_analytics_shane' in json_data
            assert 'profile_main' in json_data['google_analytics_shane']
            assert 'account' in json_data['google_analytics_shane']
            assert 'account_name' in json_data['google_analytics_shane']
            self.profile_main = json_data['google_analytics_shane']['profile_main']
            self.account = json_data['google_analytics_shane']['account']
            self.account_name = json_data['google_analytics_shane']['account_name']


class TestGA:
    gaValues = GAValues()
    globalGAWrapper = GoogleAnalyticsWrapper(profile_id=gaValues.profile_main)


class GoogleAnalyticsTests(unittest.TestCase):

    def setUp(self):
        TestGA.globalGAWrapper.set_date_range(datetime(2016,2,1), datetime(2016,2,29))
        assert TestGA.globalGAWrapper.get_start_date() == '2016-02-01'
        assert TestGA.globalGAWrapper.get_end_date() == '2016-02-29'

    def test_get_campaign_sessions_users(self):
        start_date = datetime(2015,month=1,day=1)
        end_date = datetime(2016,month=3,day=1)
        TestGA.globalGAWrapper.set_date_range(start_date, end_date)
        sessions, sessions_new_user, sessions_returning_user = TestGA.globalGAWrapper.get_total_sesssion_campaign('www.event-tracking.com')
        assert sessions == 84
        assert sessions_new_user == 84
        assert sessions_returning_user == None

        total_users, new_users= TestGA.globalGAWrapper.get_total_users_campaign('www.event-tracking.com')
        assert total_users == 84
        assert new_users == 84

        total_users, new_users= TestGA.globalGAWrapper.get_total_users_campaign('doesntexist')
        assert total_users == 0
        assert new_users == 0

    def test_get_page_stats(self):
        start_date = datetime(2015,month=1,day=1)
        end_date = datetime(2016,month=3,day=1)
        TestGA.globalGAWrapper.set_date_range(start_date, end_date)
        values = TestGA.globalGAWrapper.get_page_stats('/blog/monitor-the-web-with-google-alerts-and-slack-screenshots/')

        assert 'ga:visits' in values
        assert 'ga:pageViews' in values
        assert 'ga:uniquePageViews' in values
        assert 'ga:newUsers' in values
        assert 'ga:bounceRate' in values
        assert 'ga:avgTimeOnPage' in values
        assert 'ga:entrances' in values

        assert values['ga:visits'] == '122'
        assert values['ga:pageViews'] == '144'
        assert values['ga:uniquePageViews'] == '130'
        assert values['ga:newUsers'] == '116'
        assert values['ga:bounceRate'] == '91.80327868852459'
        assert values['ga:avgTimeOnPage'] == '313.52941176470586'
        assert values['ga:entrances'] == '122'

    def test_get_url_path_param(self):
        url1 = 'http://intellitect.com/building-single-page-applications-spa-with-the-journey-framework/'
        url2 = 'http://intellitect.com/building-single-page-applications-spa-with-the-journey-framework/?utm_source=social&utm_medium=blog%20article&utm_campaign=Building%20Single%20Page%20Applications%20(SPA)%20with%20the%20Journey%20Framework%20%2F%20Grant%20Erickson'
        intended_path = '/building-single-page-applications-spa-with-the-journey-framework/'

        assert GoogleAnalyticsWrapper.get_url_path(url1) == intended_path
        assert GoogleAnalyticsWrapper.get_url_path(url2) == intended_path

        assert GoogleAnalyticsWrapper.get_url_param(url2, 'utm_source') == 'social'
        assert GoogleAnalyticsWrapper.get_url_param(url2, 'utm_medium') == 'blog article'
        assert GoogleAnalyticsWrapper.get_url_param(url2, 'utm_campaign') == 'Building Single Page Applications (SPA) with the Journey Framework / Grant Erickson'

    def test_get_google_url(self):
        url = GoogleAnalyticsWrapper.get_google_url(url='www.test.com/testpath/',
                                                    source='testSource',
                                                    medium='testMedium',
                                                    name='testCampaignName')
        assert url == 'www.test.com/testpath/?utm_source=testSource&utm_medium=testMedium&utm_campaign=testCampaignName'

        url = GoogleAnalyticsWrapper.get_google_url(url='www.test.com/testpath/',
                                                    source='testsource',
                                                    medium='testmedium',
                                                    name='name/testcampaign')
        assert url == 'www.test.com/testpath/?utm_source=testsource&utm_medium=testmedium&utm_campaign=name%2Ftestcampaign'

        self.assertRaises(SyntaxError, GoogleAnalyticsWrapper.get_google_url,
                                      'www.test.com/testpath',
                                      'testsource',
                                      'testmedium',
                                      'name/testcampaign')
        self.assertRaises(SyntaxError, GoogleAnalyticsWrapper.get_google_url,
                                      'www.test.com/testpath',
                                      'test source',
                                      'testmedium',
                                      'name/testcampaign')
        self.assertRaises(SyntaxError, GoogleAnalyticsWrapper.get_google_url,
                                      'www.test.com/testpath',
                                      'testsource',
                                      'test medium',
                                      'name/testcampaign')
        self.assertRaises(SyntaxError, GoogleAnalyticsWrapper.get_google_url,
                                        'www.test.com/testpath',
                                        'testsource',
                                        'testmedium',
                                        'name /testcampaign')

    def test_initial_start_end_dates(self):
        start_date = (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        temp = GoogleAnalyticsWrapper()
        assert temp.get_start_date() == start_date
        assert temp.get_end_date() == end_date

    def test_initialized_test_object(self):
        TestGA.globalGAWrapper.profile_id == TestGA.gaValues.profile_main

    def test_get_first_profile_id(self):
        assert TestGA.globalGAWrapper.get_first_profile_id() == TestGA.gaValues.profile_main

    def test_init_without_profile_id(self):
        assert GoogleAnalyticsWrapper().profile_id == TestGA.globalGAWrapper.get_first_profile_id()

    def test_get_account_by_id(self):
        account = TestGA.globalGAWrapper.get_account_by_id(TestGA.gaValues.account)
        assert account['name'] == TestGA.gaValues.account_name

    def test_ga_get(self):
        result = TestGA.globalGAWrapper.ga_get(metrics='ga:users',
                                               dimensions='ga:date',
                                               max_results=40)
        assert len(result['rows']) == 29
        assert result['rows'][0][1] == '3'
        assert result['query']['start-date'] == '2016-02-01'
        assert result['query']['end-date'] == '2016-02-29'
        assert result['query']['ids'] == 'ga:{}'.format(TestGA.gaValues.profile_main)
        assert result['query']['max-results'] == 40
        assert result['query']['metrics'][0] == 'ga:users'
        assert result['query']['max-results'] == 40
        assert result['query']['max-results'] == 40
        assert result['query']['max-results'] == 40
        assert result['query']['max-results'] == 40
        assert result['totalsForAllResults']['ga:users'] == '75'

    def test_get_pageviews_source(self):
        page_views, unique_page_views, source_mediums = TestGA.globalGAWrapper.get_pageviews_source('/blog/kanban-vs-scrum-pull-vs-push/')
        assert page_views == 38
        assert unique_page_views == 35
        assert len(source_mediums) == 5
        assert source_mediums[0][0] == 'google / organic'
        assert source_mediums[0][1] == '31'
        assert source_mediums[0][2] == '29'
        assert source_mediums[0][3] == '26'
        assert source_mediums[0][4] == '96.42857142857143'
        assert source_mediums[0][5] == '43.0'
        assert source_mediums[0][6] == '28'

        page_views, unique_page_views, source_mediums = TestGA.globalGAWrapper.get_pageviews_source('doesntexist')
        assert page_views is None
        assert unique_page_views is None
        assert source_mediums is None


    def test_get_top_keywords(self):
        total_visits, keyword_list = TestGA.globalGAWrapper.get_top_keywords()
        assert total_visits == 33
        assert len(keyword_list) == 2
        assert keyword_list[0][0] == 'google'
        assert keyword_list[0][1] == '(not provided)'
        assert keyword_list[0][2] == '32'
        assert keyword_list[1][0] == 'bing'
        assert keyword_list[1][1] == 'agile + push system'
        assert keyword_list[1][2] == '1'

    def test_get_total_sessions(self):
        total_sessions, session_list = TestGA.globalGAWrapper.get_sessions()
        assert total_sessions == '81'
        assert len(session_list) == 29
        assert session_list[0][0] == '20160201' # date
        assert session_list[0][1] == '3' # count

    def test_get_total_users(self):
        total_users, user_list = TestGA.globalGAWrapper.get_users()
        assert total_users == '75'
        assert len(user_list) == 29
        assert user_list[0][0] == '20160201' # date
        assert user_list[0][1] == '3' # count

    def test_get_total_users(self):
        total_users, new_users = TestGA.globalGAWrapper.get_total_users()
        assert total_users == 71
        assert new_users == 66

    def test_get_total_sessions(self):
        sessions, sessions_new_user, sessions_returning_user = TestGA.globalGAWrapper.get_total_sessions()
        assert sessions == 81
        assert sessions_new_user == 66
        assert sessions_returning_user == 15

    def test_convert_duration_to_minutes_seconds(self):
        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(90)
        assert minutes == 1
        assert seconds == 30

        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(91.54545454545455)
        assert minutes == 1
        assert seconds == 31

        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(20)
        assert minutes == 0
        assert seconds == 20

        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(60)
        assert minutes == 1
        assert seconds == 0

        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(59)
        assert minutes == 0
        assert seconds == 59

        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(61)
        assert minutes == 1
        assert seconds == 1


    def test(self):
        results = TestGA.globalGAWrapper.ga_get('ga:users')
        assert results['totalsForAllResults']['ga:users'] == '71'
        results = TestGA.globalGAWrapper.ga_get(metrics='ga:users,ga:newUsers')
        assert results['totalsForAllResults']['ga:users'] == '71'
        assert results['totalsForAllResults']['ga:newUsers'] == '66'

        # THIS QUERY GIVES INCORRECT/UNEXPECTED DATA (verified on GOOGLE ANALYTICS)
        results = TestGA.globalGAWrapper.ga_get(metrics='ga:users',dimensions='ga:userType')
        assert results['totalsForAllResults']['ga:users'] == '74' # NOT 71, as above!
        assert results['rows'][0][0] == 'New Visitor'
        assert results['rows'][0][1] == '66'
        assert results['rows'][1][0] == 'Returning Visitor'
        assert results['rows'][1][1] == '8'
        for row in results['rows']:
            if row[0] == 'New Visitor':
                assert row[1] == '66'
            elif row[0] == 'Returning Visitor':
                assert row[1] == '8'
            else:
                raise LookupError('unexpected value')
        results = TestGA.globalGAWrapper.ga_get(metrics='ga:visits',
                              dimensions='ga:source,ga:keyword',
                              sort='-ga:visits',
                              filters='ga:medium==organic',
                              max_results=10)
        results = TestGA.globalGAWrapper.ga_get(metrics='ga:visits',
                              dimensions='ga:source,ga:keyword',
                              sort='-ga:visits',
                              max_results=10)
        results = TestGA.globalGAWrapper.ga_get(metrics='ga:entrances',
                              dimensions='ga:keyword',
                              sort='-ga:entrances',
                              max_results=10)
        results = TestGA.globalGAWrapper.ga_get(metrics='ga:users',
                              max_results=10)

        assert True


def print_results(results):
  """Prints out the results.

  This prints out the profile name, the column headers, and all the rows of
  data.

  Args:
    results: The response returned from the Core Reporting API.
  """

  print()
  print('Profile Name: %s' % results.get('profileInfo').get('profileName'))
  print()

  # Print header.
  output = []
  for header in results.get('columnHeaders'):
    output.append('%30s' % header.get('name'))
  print(''.join(output))

  # Print data table.
  if results.get('rows', []):
    for row in results.get('rows'):
      output = []
      for cell in row:
        output.append('%30s' % cell)
      print(''.join(output))

  else:
    print('No Rows Found')


if __name__ == '__main__':
    unittest.main()
