import unittest
import json
import oauth2

class MyTest(unittest.TestCase):
    def test_rate_limit(self):
        resp, content = oauth_req('https://api.twitter.com/1.1/application/rate_limit_status.json')
        rate_limit_remaining = content['resources']['application']['/application/rate_limit_status']['remaining']
        assert rate_limit_remaining > 0
        print("Rate Limit (/application/rate_limit_status): {}".format(rate_limit_remaining))
        print(content)
        print("==================================")

    def test_search_api(self):
        """https://dev.twitter.com/rest/public/search"""
        resp, content = oauth_req('https://api.twitter.com/1.1/search/tweets.json?q=shanekercheval')
        assert resp.status == 200
        assert len(content['statuses']) > 0
        for status in content['statuses']:
            print("'{}' .... {}".format(status['text'], status['source']))

        resp, content = oauth_req('https://api.twitter.com/1.1/application/rate_limit_status.json')
        rate_limit_remaining = content['resources']['search']['/search/tweets']['remaining']
        assert rate_limit_remaining > 0
        print("Rate Limit (/search/tweets): {}".format(rate_limit_remaining))
        print("==================================")

    def test_users_show(self):
        """https://dev.twitter.com/rest/reference/get/users/show"""
        resp, content = oauth_req('https://api.twitter.com/1.1/users/show.json?screen_name=shanekercheval')
        assert resp.status == 200
        assert content['name'] == 'Shane Kercheval'
        print("name: {}".format(content['name']))
        assert content['followers_count'] > 30
        print("followers_count: {}".format(content['followers_count']))
        assert content['location'] == 'Spokane, Wa'
        print("location: {}".format(content['location']))
        assert content['statuses_count'] > 180
        print("statuses_count: {}".format(content['statuses_count']))

        resp, content = oauth_req('https://api.twitter.com/1.1/application/rate_limit_status.json')
        rate_limit_remaining = content['resources']['users']['/users/show/:id']['remaining']
        assert rate_limit_remaining > 0
        print("Rate Limit (/users/show/:id): {}".format(rate_limit_remaining))
        print("==================================")


def oauth_req(url, http_method="GET", post_body="", http_headers=None):
    with open('../../settings/credentials.json') as json_file:
        json_data = json.load(json_file)
        assert 'twitter' in json_data
        assert 'CONSUMER_KEY' in json_data['twitter']
        assert 'CONSUMER_SECRET' in json_data['twitter']
        assert 'APP_KEY' in json_data['twitter']
        assert 'APP_SECRET' in json_data['twitter']
        consumer_key = json_data['twitter']['CONSUMER_KEY']
        consumer_secret = json_data['twitter']['CONSUMER_SECRET']
        app_key = json_data['twitter']['APP_KEY']
        app_secret = json_data['twitter']['APP_SECRET']

    """https://dev.twitter.com/oauth/overview/single-user"""
    consumer = oauth2.Consumer(key=consumer_key, secret=consumer_secret)
    token = oauth2.Token(key=app_key, secret=app_secret)
    client = oauth2.Client(consumer, token)
    resp, content = client.request(url, method=http_method, body=post_body.encode('utf-8'), headers=http_headers)

    json_data = json.loads(content.decode('utf-8'))

    return resp, json_data


if __name__ == '__main__':
    unittest.main()
