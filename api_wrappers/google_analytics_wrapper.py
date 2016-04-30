import urllib.parse
from datetime import timedelta, datetime
from googleapiclient import sample_tools


class GoogleAnalyticsWrapper:

    def get_sessions(self):
        """
        :return: total number of sessions and a list of sessions for each date
        """
        results = self.ga_get(metrics='ga:sessions',dimensions='ga:date')
        total_sessions = results['totalsForAllResults']['ga:sessions']
        session_list = results['rows']
        return total_sessions, session_list

    def get_total_sesssion_campaign(self, campaign_name):
        return self.get_total_sessions(filters='ga:campaign=={}'.format(campaign_name))

    def get_total_sessions(self, filters=None):
        """
        :return: 2 values: 1) total users 2) new_users
        """
        results = self.ga_get(metrics='ga:sessions',
                              dimensions='ga:userType',
                              filters=filters)
        sessions = int(results['totalsForAllResults']['ga:sessions'])
        sessions_new_user = None
        sessions_returning_user = None
        for row in results['rows']:
            if row[0] == 'New Visitor':
                sessions_new_user = int(row[1])
            elif row[0] == 'Returning Visitor':
                sessions_returning_user = int(row[1])
            else:
                raise LookupError('unexpected value in get_total_sessions')
        return sessions, sessions_new_user, sessions_returning_user

    def get_users(self):
        """
        :return: total number of users and a list of sessions for each date
        """
        results = self.ga_get(metrics='ga:users',dimensions='ga:date')
        total_sessions = results['totalsForAllResults']['ga:users']
        session_list = results['rows']
        return total_sessions, session_list

    def get_total_users(self, filters=None):
        """
        :return: 2 values: 1) total users 2) new_users
        """
        results = self.ga_get(metrics='ga:users,ga:newUsers', filters=filters)
        total_users = int(results['totalsForAllResults']['ga:users'])
        new_users = int(results['totalsForAllResults']['ga:newUsers'])
        return total_users, new_users

    def get_total_users_campaign(self, campaign_name):
        return self.get_total_users(filters='ga:campaign=={}'.format(campaign_name))

    def get_page_stats(self, url_path):
        results = self.ga_get(metrics='ga:visits,ga:pageViews,ga:uniquePageViews,ga:newUsers,ga:bounceRate,ga:avgTimeOnPage,ga:entrances',
                              filters='ga:pagePath=={}'.format(url_path))

        return results['totalsForAllResults']

    def get_pageviews_source(self, url_path):
        results = self.ga_get(metrics="ga:pageViews,ga:uniquePageViews,ga:newUsers,ga:bounceRate,ga:avgTimeOnPage,ga:entrances",
                              dimensions="ga:sourceMedium",
                              filters='ga:pagePath=={}'.format(url_path))
        if 'rows' not in results:
            return None, None, None

        page_views = results['totalsForAllResults']['ga:pageViews']
        unique_page_views = results['totalsForAllResults']['ga:uniquePageViews']
        source_mediums = results['rows']
        source_mediums = sorted(source_mediums,key=lambda l:int(l[1]), reverse=True)
        return int(page_views), int(unique_page_views), source_mediums

    def get_top_keywords(self, max_results=10):
        results = self.ga_get(metrics='ga:visits',
                              dimensions='ga:source,ga:keyword',
                              sort='-ga:visits',
                              filters='ga:medium==organic',
                              max_results=max_results)
        total_visits = int(results['totalsForAllResults']['ga:visits'])
        keywords = results['rows']
        return total_visits, keywords

    def ga_get(self,
               metrics,
               ids=None,
               start_date=None,
               end_date=None,
               dimensions=None,
               sort=None,
               filters=None,
               segment=None,
               samplingLevel=None,
               include_empty_rows=None,
               start_index=None,
               max_results=50,
               output=None,
               fields=None,
               prettyPrint=None,
               userIp=None,
               quotaUser=None,
               key=None):
        return self.service.data().ga().get(
            ids=ids or 'ga:' + self.profile_id,
            start_date=start_date or self.get_start_date(),
            end_date=end_date or self.get_end_date(),
            metrics=metrics,
            dimensions=dimensions,
            sort=sort,
            filters=filters,
            segment=segment,
            samplingLevel=samplingLevel,
            include_empty_rows=include_empty_rows,
            start_index=start_index,
            max_results=max_results,
            output=output,
            fields=fields,
            prettyPrint=prettyPrint,
            userIp=userIp,
            quotaUser=quotaUser,
            key=key
            ).execute()

    def get_account_by_id(self, id):
        """
        returns the account based on the id
        :param id: (GA -> Admin -> Account ID)
        :return dictionary
        """
        accounts = self.service.management().accounts().list().execute()['items']
        for account in accounts:
            if account['id'] == id:
                return account

        return None

    def get_first_profile_id(self):
        """Traverses Management API to return the first profile id.

        This first queries the Accounts collection to get the first account ID.
        This ID is used to query the Webproperties collection to retrieve the first
        webproperty ID. And both account and webproperty IDs are used to query the
        Profile collection to get the first profile id.

        Args:
        service: The service object built by the Google API Python client library.

        Returns:
        A string with the first profile ID. None if a user does not have any
        accounts, webproperties, or profiles.
        """

        accounts = self.service.management().accounts().list().execute()

        if accounts.get('items'):
            firstAccountId = accounts.get('items')[0].get('id')
            webproperties = self.service.management().webproperties().list(
                accountId=firstAccountId).execute()

        if webproperties.get('items'):
            firstWebpropertyId = webproperties.get('items')[0].get('id')
            profiles = self.service.management().profiles().list(
                accountId=firstAccountId,
                webPropertyId=firstWebpropertyId).execute()

        if profiles.get('items'):
            return profiles.get('items')[0].get('id')

        return None

    def set_date_range(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def get_end_date(self):
        return self.end_date.strftime('%Y-%m-%d')

    def get_start_date(self):
        return self.start_date.strftime('%Y-%m-%d')

    def __init__(self, profile_id=None):
        self.service, self.flags = sample_tools.init(
                [], 'analytics', 'v3', __doc__, __file__,
                scope='https://www.googleapis.com/auth/analytics.readonly')

        if profile_id is None:
            self.profile_id = self.get_first_profile_id()
        else:
            self.profile_id = profile_id

        self.start_date=(datetime.now()-timedelta(days=30))
        self.end_date=datetime.now()

    @staticmethod
    def get_google_url(url, source, medium, name):
        """
        :param url: the url you want to add campaign info to
        :param source: "Every referral to a web site has an origin, or source. Possible sources include: “google” (the name of a search engine), “facebook.com” (the name of a referring site), “spring_newsletter” (the name of one of your newsletters), and “direct” (users that typed your URL directly into their browser, or who had bookmarked your site)."
        :param medium: "Every referral to a website also has a medium. Possible medium include: “organic” (unpaid search), “cpc” (cost per click, i.e. paid search), “referral” (referral), “email” (the name of a custom medium you have created), “none” (direct traffic has a medium of “none”). "
        :param name: "'name' is the name of the referring AdWords campaign or a custom campaign that you have created."
        :return: url with campaign parameters
        """
        if url[-1:] != '/':
            raise SyntaxError('last character should be "/" in {}'.format(url))
        if " " in source or " " in medium or " " in name:
            raise SyntaxError('space found in parameter: {}, {}, {}'.format(source, medium, name))
        return "{}?{}&{}&{}".format(url,
                                   urllib.parse.urlencode({'utm_source': source}),
                                   urllib.parse.urlencode({'utm_medium': medium}),
                                   urllib.parse.urlencode({'utm_campaign': name}))

    @staticmethod
    def get_url_path(url):
        path = urllib.parse.urlsplit(url)
        return path[2]

    @staticmethod
    def get_url_param(url, param):
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        return params[param][0]

    @staticmethod
    def convert_duration_to_minutes_seconds(time):
        total_seconds = int(time)
        minutes = int(total_seconds / 60)
        seconds = total_seconds % 60
        return minutes, seconds