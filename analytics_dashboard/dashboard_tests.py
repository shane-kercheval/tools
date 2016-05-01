import json
import unittest
import urllib.parse
import html
import googleapiclient
import calendar
from datetime import timedelta, datetime
from api_wrappers.google_analytics_wrapper import GoogleAnalyticsWrapper
from api_wrappers.bitly_wrapper import Bitly
from api_wrappers.mailchimp_wrapper import MailchimpWrapper


class WebsiteInfo:
    def __init__(self, name, google_analytics_profile_id):
        self.name = name
        self.google_analytics_profile_id = google_analytics_profile_id
        self.ga_wrapper = GoogleAnalyticsWrapper(profile_id=self.google_analytics_profile_id)


class Account:
    def __init__(self, name, excel_file_path, bitly_username, bitly_password, mailchimp_api_key, websites):
        self.name = name
        self.excel_file_path = excel_file_path
        self.bitly_username = bitly_username
        self.bitly_password = bitly_password
        self.mailchimp_api_key = mailchimp_api_key
        self.websites = websites


class Info:
    def __init__(self):
        with open('../../settings/dashboard.json') as json_file:
            self.accounts = []

            json_data = json.load(json_file)
            assert 'accounts' in json_data
            for account in json_data['accounts']:
                websites = []
                for website in account['websites']:
                    websites.append(WebsiteInfo(name=website['website_name'],
                                                google_analytics_profile_id=website['google_analytics_profile_id']))

                self.accounts.append(Account(
                    name=account['name'],
                    excel_file_path=account['excel_file_path'],
                    bitly_username=account['bitly_username'],
                    bitly_password=account['bitly_password'],
                    mailchimp_api_key=account['mailchimp_api_key'],
                    websites=websites
                ))


class Globals:
    info = Info()


class IntelliTectBlogArticlesTests(unittest.TestCase):

    def test_dashboard_json(self):
        assert len(Globals.info.accounts) > 0
        assert Globals.info.accounts[0].name == "IntelliTect"
        assert Globals.info.accounts[0].bitly_username is not None
        assert Globals.info.accounts[0].bitly_password is not None
        assert Globals.info.accounts[0].mailchimp_api_key is not None
        assert Globals.info.accounts[0].excel_file_path is not None
        assert len(Globals.info.accounts[0].websites) == 2

        for account in Globals.info.accounts:
            print("--------------account: {}-----------".format(account.name))
            print("excel path: {}".format(account.excel_file_path))
            print("bitly username: {}".format(account.bitly_username))
            print("bitly password: {}".format(account.bitly_password))
            print("mailchimp_api_key: {}".format(account.mailchimp_api_key))

            for website in account.websites:
                assert website.name is not None
                assert website.google_analytics_profile_id is not None
                assert website.ga_wrapper is not None
                print("    ---website_name: {}".format(website.name))
                print("       google_analytics_profile_id: {}".format(website.google_analytics_profile_id))
        print()

    def test_website(self):
        # for each account, for each website within each account, update xlsx
        for account in Globals.info.accounts:
            for website in account.websites:
                print('------WEBSITE: {}------'.format(website.name))
                workbook, worksheet, headers = open_workbook_worksheet(account.excel_file_path, website.name)

                # get metrics, dimensions, sort, filter, max results
                configurations = {'metrics': [],
                                  'dimensions': [],
                                  'sort': [],
                                  'filters': [],
                                  'max_results': [],
                                  'display_dimension': [],
                                  'index': [],
                                  }
                for column in worksheet.columns[:7]:
                    # print(column[0].value)
                    current_column_name = column[0].value
                    for row in column[1:]:
                        configurations[current_column_name].append(row.value)

                assert len(configurations['metrics']) == \
                       len(configurations['dimensions']) == \
                       len(configurations['sort']) == \
                       len(configurations['filters']) == \
                       len(configurations['max_results']) == \
                       len(configurations['display_dimension']) == \
                       len(configurations['index'])
                print('------')

                for column in worksheet.columns[8:]:
                    start_date = datetime.strptime(column[0].value, '%Y-%m')
                    last_day = calendar.monthrange(start_date.year, start_date.month)[1]
                    end_date = datetime(year=start_date.year, month=start_date.month, day=last_day)
                    website.ga_wrapper.set_date_range(start_date=start_date, end_date=end_date)
                    print("website date: {} - {}".format(start_date, end_date))

                    cached_data = None
                    row_index = 0
                    for row in column[1:]:
                        if row.value is None: # only update empty cells
                            metrics = configurations['metrics'][row_index]
                            index = configurations['index'][row_index]

                            if metrics is None:
                                if index is None:
                                    row_index += 1
                                    continue
                                else: # display index
                                    if cached_data is not None and len(cached_data) >= index: # check to make sure there was enough data returned
                                        cached_data_row = cached_data[index -1]
                                        row.value = "{}% - {} ({})".format(round(cached_data_row[2]*100), cached_data_row[0], cached_data_row[1]) # get the data

                            else: # we only want to go out to GA and get results if we are not retrieving cached data and we have metrics
                                dimensions = configurations['dimensions'][row_index]
                                sort = configurations['sort'][row_index]
                                filters = configurations['filters'][row_index]
                                max_results = configurations['max_results'][row_index]
                                display_dimension = configurations['display_dimension'][row_index]
                                if max_results is not None and column[row_index+2].value is not None: # if we are getting ready to go cache results, if the next row is already filled (is not None), then we don't need to.
                                    print("SKIPPED: {} - {}".format(metrics, dimensions))
                                    row_index += 1
                                    continue

                                print("{} - {}".format(metrics, dimensions))
                                results = website.ga_wrapper.ga_get(metrics=metrics,
                                                           dimensions=dimensions,
                                                           sort=sort,
                                                           filters=filters,
                                                           max_results=max_results)
                                metrics_parts = metrics.split(',')
                                if max_results is not None: # we need to save the 'results' array, no cell updates necessary
                                    total_results = float(results['totalsForAllResults'][metrics])
                                    if 'rows' not in results:
                                        cached_data = []
                                    else:
                                        cached_data = results['rows']
                                    for data in cached_data:
                                        data.append(float(data[1])/total_results)
                                elif len(metrics_parts) == 1:
                                    if display_dimension is not None:
                                        for result_row in results['rows']:
                                            if display_dimension == result_row[0]:
                                                row.value = float(result_row[1])
                                    else:
                                        row.value = float(results['totalsForAllResults'][metrics])
                                else:
                                    raise IndexError("unsupported number of metrics: {}".format(metrics))
                        row_index += 1

                workbook.save(account.excel_file_path)

    def test_campaigns(self):
        for account in Globals.info.accounts:
            workbook, worksheet, headers = open_workbook_worksheet(account.excel_file_path, 'campaigns')
            mailchimp = MailchimpWrapper(api_key=account.mailchimp_api_key)
            bitly_wrapper = Bitly()
            bitly_wrapper.authenticate_http_basic_auth(username=account.bitly_username,
                                                       password=account.bitly_password)

            # get headers, i.e. definitions of columns per type
            headers = {}

            for row in worksheet.rows[:3]:
                headers[row[0].value] = []
                for column in row[1:]:
                    if  column.value is not None:
                        headers[row[0].value].append(column.value)

            campaign_date = None
            campaign_duration = None

            for row in worksheet.rows[5:]:
                # determine if it is a link, a campaign, or blank
                if row[0].value is None:
                    continue

                split = row[0].value.split('|')
                if len(row[0].value) == len('XXXX-XX-XX'):
                    campaign_date = datetime.strptime(row[0].value, '%Y-%m-%d')
                    campaign_duration = row[2].value
                elif len(split) > 1:
                    type = split[0]
                    data = split[1]

                    if type == 'bitly':
                        #if row[2].value is None:
                        row[2].value = bitly_wrapper.get_total_clicks(bitly=data)
                        row[3].value = bitly_wrapper.get_target_url(bitly=data)
                    elif type == 'mailchimp':
                        campaign = mailchimp.get_campaign(campaign_id=data)
                        column_index = 2
                        for column_name in headers['mailchimp']:
                            parts = column_name.split('/')
                            if len(parts) == 1:
                                if column_name in campaign:
                                    row[column_index].value = campaign[column_name]
                                else:
                                    row[column_index].value = "-"
                            elif len(parts) == 2:
                                if parts[0] in campaign and parts[1] in campaign[parts[0]]:
                                    row[column_index].value = campaign[parts[0]][parts[1]]
                                else:
                                    row[column_index].value = '-'
                            else:
                                raise ValueError("path ({}) has invalid number of parts, invalid".format(column_name))
                            column_index += 1
                    elif type == 'analytics':
                        end_date = campaign_date + timedelta(days=campaign_duration)
                        account.websites[0].ga_wrapper.set_date_range(start_date=campaign_date, end_date=datetime.today())
                        long_term_page_stats = account.websites[0].ga_wrapper.get_page_stats(GoogleAnalyticsWrapper.get_url_path(data))

                        row[2].value = long_term_page_stats['ga:newUsers']
                        row[3].value = long_term_page_stats['ga:entrances']
                        row[4].value = long_term_page_stats['ga:uniquePageViews']
                        row[5].value = long_term_page_stats['ga:bounceRate']
                        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(float(long_term_page_stats['ga:avgTimeOnPage']))
                        row[6].value = "{}:{}".format(minutes, seconds)

                        # executes every time to keep a running total
                        source_page_views, source_unique_page_views, source_mediums = account.websites[0].ga_wrapper.get_pageviews_source(GoogleAnalyticsWrapper.get_url_path(data))
                        row[7].value = source_unique_page_views or 'Not Found'

                        if source_mediums is None or len(source_mediums) < 1:
                            row[8].value = "Not Found"
                        else:
                            row[8].value = "{}: {}".format(source_mediums[0][0],
                                                        source_mediums[0][6])

                        if source_mediums is None or len(source_mediums) < 2:
                            row[9].value = "Not Found"
                        else:
                            row[9].value = "{}: {}".format(source_mediums[1][0],
                                                        source_mediums[1][6])
                        # get duration stats
                        account.websites[0].ga_wrapper.set_date_range(start_date=campaign_date, end_date=end_date)
                        duration_page_stats = account.websites[0].ga_wrapper.get_page_stats(GoogleAnalyticsWrapper.get_url_path(data))

                        row[10].value = duration_page_stats['ga:newUsers']
                        row[11].value = duration_page_stats['ga:entrances']
                        row[12].value = duration_page_stats['ga:uniquePageViews']
                        row[13].value = duration_page_stats['ga:bounceRate']
                        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(float(duration_page_stats['ga:avgTimeOnPage']))
                        row[14].value = "{}:{}".format(minutes, seconds)
                    else:
                        raise IndexError('unknown type: {}'.format(type))
                else: # assume date
                    raise IndexError('unknown type(row): {}'.format(row[0].value))

            workbook.save(account.excel_file_path)

    def test_newsletter_links(self):
        for account in Globals.info.accounts:
            workbook, worksheet, headers = open_workbook_worksheet(account.excel_file_path, 'newsletter_links')
            mailchimp = MailchimpWrapper(api_key=account.mailchimp_api_key)

            google_source = 'newsletter'
            google_medium = 'email'
            account_google_campaign = None
            non_account_google_campaign = account.websites[0].name

            campaign_links = None
            newsletter_campaign_id = None

            for row in worksheet.rows[1:]:
                link = None
                header = None
                text = None
                google_url = None

                column_index = 0
                for column in row:
                    if headers[column_index] == 'newsletter_campaign_id' and column.value is not None:
                        newsletter_campaign_id = column.value
                        if len(newsletter_campaign_id) > 3:
                            account_google_campaign = row[1].value.replace(' ', '-')
                            campaign_links = mailchimp.get_campaign_links(campaign_id=newsletter_campaign_id)
                            assert campaign_links['campaign_id'] == newsletter_campaign_id
                        break
                    elif headers[column_index] == 'link':
                        if column.value[-1:] != '/':
                            column.value = column.value+'/'
                        link = column.value
                    elif headers[column_index] == 'header':
                        header = column.value
                    elif headers[column_index] == 'text':
                        text = column.value
                    elif headers[column_index] == 'google_url':
                        if column.value is None:
                            campaign_name = account_google_campaign if is_account_domain(link, account.websites[0].name) else non_account_google_campaign
                            column.value = GoogleAnalyticsWrapper.get_google_url(
                                url=link,
                                source=google_source,
                                medium=google_medium,
                                name=campaign_name)
                        google_url = column.value
                    elif headers[column_index] == 'header_num_chars' and column.value is None:
                        assert header is not None
                        column.value = len(header)
                    elif headers[column_index] == 'text_num_chars' and column.value is None:
                        assert text is not None
                        column.value = len(text)
                    elif headers[column_index] == 'mailchimp_html' and column.value is None:
                        assert google_url is not None
                        assert header is not None
                        assert text is not None
                        column.value = encode_html(url=link, header=header, text=text)

                        #else:
                        #raise IndexError()
                    elif headers[column_index] == 'is_domain':
                        column.value = is_account_domain(url=link, website_name=account.websites[0].name)
                    elif headers[column_index].split('/')[0] == 'mailchimp':
                        if len(newsletter_campaign_id) > 3 and len(campaign_links['urls_clicked']) > 0:
                            field = headers[column_index].split('/')[1]
                            column.value = get_mailchimp_link_field(
                                field=field,
                                campaign_links=campaign_links,
                                link=google_url,
                                newsletter_campaign_id=newsletter_campaign_id)

                    column_index += 1
                print("{} - {} - {} - {} - {}".format(newsletter_campaign_id, account_google_campaign, link, header, text))

            workbook.save(account.excel_file_path)

    def test_newsletters(self):
        for account in Globals.info.accounts:
            workbook, worksheet, headers = open_workbook_worksheet(account.excel_file_path, 'newsletters')
            mailchimp = MailchimpWrapper(api_key=account.mailchimp_api_key)

            for row in worksheet.rows[1:]:
                campaign_id = row[0].value
                print("id: {}".format(campaign_id))
                campaign = mailchimp.get_campaign(campaign_id=campaign_id)
                campaign_report = mailchimp.get_campaign_report(campaign_id=campaign_id)
                assert campaign['id'] == campaign_id

                column_index = 0
                for column in row:
                    if column_index == 0:
                        column_index += 1
                        continue
                    elif headers[column_index] == 'a/b tested':
                        column.value = 'variate_settings' in campaign
                    else:
                        path = headers[column_index]
                        parts = path.split('/')

                        if parts[0] == 'report':
                            column.value = campaign_report[parts[1]]
                        else:
                            if len(parts) == 1:
                                if path in campaign:
                                    column.value = campaign[path]
                                else:
                                    column.value = "-"
                            elif len(parts) == 2:
                                if parts[0] in campaign and parts[1] in campaign[parts[0]]:
                                    column.value = campaign[parts[0]][parts[1]]
                                else:
                                    column.value = '-'
                            else:
                                raise ValueError("path ({}) has invalid number of parts, invalid".format(path))
                    column_index += 1
            workbook.save(account.excel_file_path)

    def test_blog_articles(self):
        for account in Globals.info.accounts:

            workbook, worksheet, headers = open_workbook_worksheet(account.excel_file_path, 'blog_articles')
            number_of_days_stats_collected = 30
            bitly_wrapper = Bitly()
            bitly_wrapper.authenticate_http_basic_auth(account.bitly_username, account.bitly_password)

            for row in worksheet.rows[1:]:
                column_index = 0
                article_name = None
                author = None
                start_date = None
                end_date = None
                url = None
                source = None
                medium = None
                campaign = None
                google_url = None
                bitly_link = None
                ga_page_stats = None
                long_term_page_stats = None
                campaign_total_users = None
                campaign_new_users = None
                source_mediums = None
                for col in row:
                    column_name = headers[column_index]

                    if column_name == 'name':
                        article_name = col.value
                        assert article_name is not None
                    elif column_name == 'author':
                        author = col.value
                        assert author is not None
                    elif column_name == 'date':
                        start_date = col.value
                        end_date = start_date + timedelta(days=number_of_days_stats_collected)
                        account.websites[0].ga_wrapper.set_date_range(start_date=start_date, end_date=end_date)
                        assert start_date is not None
                        assert end_date is not None
                    elif column_name == 'url':
                        url = col.value
                        assert url is not None
                    elif column_name == 'source':
                        source = col.value
                        assert source is not None
                    elif column_name == 'medium':
                        medium = col.value
                        assert medium is not None
                    elif column_name == 'campaign':
                        if col.value is None:
                            campaign = '{}/{}'.format(article_name.replace(' ', '_'), author.replace(' ', '_'))
                            col.value = campaign
                        else:
                            campaign = col.value
                        assert campaign is not None
                    elif column_name == 'Google Url':
                        if col.value is None:
                            assert url is not None
                            assert source is not None
                            assert medium is not None
                            assert campaign is not None
                            google_url = GoogleAnalyticsWrapper.get_google_url(url, source, medium, campaign)
                            col.value = google_url
                        else:
                            google_url = col.value
                        assert google_url is not None
                    elif column_name == 'bitly':
                        if col.value is None:
                            # 2 cases, it exists already, or we need to create it. Try to create, if we get Permission error, assume it already exists
                            assert google_url is not None
                            col.value = bitly_wrapper.create_or_get_bitly(google_url)
                        bitly_link = col.value
                        assert bitly_link is not None
                    elif column_name == 'ga:newUsers (at)':
                        # executes every time to keep a running total
                        account.websites[0].ga_wrapper.set_date_range(start_date=start_date, end_date=datetime.today())
                        long_term_page_stats = account.websites[0].ga_wrapper.get_page_stats(GoogleAnalyticsWrapper.get_url_path(url))
                        col.value = int(long_term_page_stats[column_name.split()[0]])
                        account.websites[0].ga_wrapper.set_date_range(start_date=start_date,end_date=end_date)
                    elif column_name == 'ga:entrances (at)':
                        assert long_term_page_stats is not None
                        col.value = int(long_term_page_stats[column_name.split()[0]])
                    elif column_name == 'ga:uniquePageViews (at)':
                        assert long_term_page_stats is not None
                        col.value = int(long_term_page_stats[column_name.split()[0]])
                    elif column_name == 'ga:bounceRate (at)':
                        assert long_term_page_stats is not None
                        col.value = float(long_term_page_stats[column_name.split()[0]])/100
                    elif column_name == 'ga:avgTimeOnPage (at)':
                        assert long_term_page_stats is not None
                        minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(float(long_term_page_stats[column_name.split()[0]]))
                        col.value = "{}:{}".format(minutes, seconds)
                    elif column_name == 'campaign total users (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            if campaign_total_users is None:
                                assert start_date is not None
                                assert end_date is not None
                                account.websites[0].ga_wrapper.set_date_range(start_date=start_date,end_date=end_date)
                                assert campaign is not None
                                try:
                                    campaign_total_users, campaign_new_users = account.websites[0].ga_wrapper.get_total_users_campaign(campaign_name=campaign)
                                except googleapiclient.errors.HttpError:
                                    campaign_new_users = "Not Found"
                                    campaign_total_users = "Not Found"
                            col.value = campaign_total_users
                    elif column_name == 'campaign new users (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            assert campaign_new_users is not None
                            col.value = campaign_new_users
                    elif column_name == 'ga:newUsers (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            if ga_page_stats is None:
                                assert start_date is not None
                                assert end_date is not None
                                account.websites[0].ga_wrapper.set_date_range(start_date=start_date,end_date=end_date)

                                assert url is not None
                                ga_page_stats = account.websites[0].ga_wrapper.get_page_stats(GoogleAnalyticsWrapper.get_url_path(url))
                                assert ga_page_stats is not None
                            col.value = int(ga_page_stats[column_name.split()[0]])
                    elif column_name == 'ga:entrances (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            assert ga_page_stats is not None
                            col.value = int(ga_page_stats[column_name.split()[0]])
                    elif column_name == 'ga:visits (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            assert ga_page_stats is not None
                            col.value = int(ga_page_stats[column_name.split()[0]])
                    elif column_name == 'ga:pageViews (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            assert ga_page_stats is not None
                            col.value = int(ga_page_stats[column_name.split()[0]])
                    elif column_name == 'ga:uniquePageViews (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            assert ga_page_stats is not None
                            col.value = int(ga_page_stats[column_name.split()[0]])
                    elif column_name == 'ga:bounceRate (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            assert ga_page_stats is not None
                            col.value = float(ga_page_stats[column_name.split()[0]])/100
                    elif column_name == 'ga:avgTimeOnPage (30d)':
                        if col.value is None and date_is_before_today(end_date):
                            assert ga_page_stats is not None
                            minutes, seconds = GoogleAnalyticsWrapper.convert_duration_to_minutes_seconds(float(ga_page_stats[column_name.split()[0]]))
                            col.value = "{}:{}".format(minutes, seconds)
                    elif column_name == 'Source Unique Page Views (at)':
                        # executes every time to keep a running total
                        account.websites[0].ga_wrapper.set_date_range(start_date=start_date, end_date=datetime.today())
                        source_page_views, source_unique_page_views, source_mediums = account.websites[0].ga_wrapper.get_pageviews_source(GoogleAnalyticsWrapper.get_url_path(url))
                        col.value = source_unique_page_views or 'Not Found'
                        account.websites[0].ga_wrapper.set_date_range(start_date=start_date,end_date=end_date)
                    elif column_name == 'Top Source':
                        if source_mediums is None or len(source_mediums) < 1:
                            col.value = "Not Found"
                        else:
                            col.value = "{}: {}".format(source_mediums[0][0], source_mediums[0][6])
                    elif column_name == 'Second Source':
                        if source_mediums is None or len(source_mediums) < 2:
                            col.value = "Not Found"
                        else:
                            col.value = "{}: {}".format(source_mediums[1][0], source_mediums[1][6])
                    elif column_name == 'Bitly Total Clicks (at)':
                        if col.value is None and date_is_before_today(end_date) and bitly_link is not None:
                            col.value = bitly_wrapper.get_total_clicks(bitly_link)
                    elif column_name == 'Bitly Facebook (at)':
                        assert True
                    elif column_name == 'Bitly Twitter (at)':
                        assert True
                    elif column_name == 'Bitly LinkedIn (at)':
                        assert True
                    else:
                        print('unknown column name: {}'.format(column_name))
                        assert False
                    #if col.value is None:
                    #    col.value = '--'
                    #print(col.value, end="\t")
                    column_index += 1
                #print('--------')
                print("date range: {} - {} -- {}".format(account.websites[0].ga_wrapper.get_start_date(), account.websites[0].ga_wrapper.get_end_date(), article_name))
            # save at end, only if everything succeeds
            workbook.save(account.excel_file_path)
            print("bitly API calls: {}".format(bitly_wrapper.get_total_api_request_count()))


def open_workbook_worksheet(workbook_name, worksheet_name):
    # https://openpyxl.readthedocs.org/en/2.5/tutorial.html
    # pip install openpyxl
    from openpyxl import load_workbook
    work_book = load_workbook(workbook_name)
    names = work_book.get_sheet_names()
    print(names)
    work_sheet = work_book[worksheet_name]

    # headers
    headers = []
    for column in work_sheet.rows[0]:
        headers.append(column.value)

    print(headers)

    return work_book, work_sheet, headers


def is_account_domain(url, website_name):
    return website_name in url.lower()


def encode_html(url, header, text):
    base_url = urllib.parse.urlparse(url)[0]+"://"+urllib.parse.urlparse(url)[1]
    return '<h3><a href="{}" target="_blank">{}</a></h3><p>{}</p><span style="font-size:12px"><em><a href="{}" target="_blank">{}</a></em></span><br />&nbsp;'.format(url, header, html.escape(text,quote=True), base_url, urllib.parse.urlparse(url)[1])


def date_is_before_today(date):
    difference = datetime.today() - date
    return difference.days >= 1


def get_mailchimp_link_field(field, campaign_links=None, link=None, newsletter_campaign_id=None):
    assert campaign_links is not None
    assert link is not None
    assert newsletter_campaign_id is not None
    target_url = '{}&mc_cid={}&mc_eid=[UNIQID]'.format(link, newsletter_campaign_id)
    assert target_url in campaign_links['urls_clicked']
    return campaign_links['urls_clicked'][target_url][field]

if __name__ == '__main__':
    unittest.main()
