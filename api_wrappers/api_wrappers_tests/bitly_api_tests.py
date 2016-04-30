import json
import unittest
from api_wrappers.bitly_wrapper import Bitly


class TestBitly:
    @staticmethod
    def get_access_token():
        with open('../../../settings/credentials.json') as json_file:
            json_data = json.load(json_file)
            assert 'bitly' in json_data
            assert 'access_token' in json_data['bitly']
            return json_data['bitly']['access_token']

    globalBitly = Bitly(access_token=get_access_token.__func__())


class MyTest(unittest.TestCase):

#    def test_create_bitly(self):
#        bitly = TestBitly.globalBitly.create_bitly('http://shanekercheval.me/contact/')
#        assert False

    def test_create_bitly_existing_url(self):
        # PermissionError: (get)json-status_code: "304";json-status_txt: "LINK_ALREADY_EXISTS"
        self.assertRaises(PermissionError, TestBitly.globalBitly.create_bitly, 'http://shanekercheval.me/contact/')
        bitlink = TestBitly.globalBitly.create_or_get_bitly('http://shanekercheval.me/contact/')
        assert bitlink == 'http://bit.ly/1RtBYed'

    def test_validate_url_for_creating(self):
        valid_url1 = 'http://intellitect.com'
        valid_url2 = 'http://intellitect.com/?utm_source=test&utm_medium=test&utm_campaign=test'
        valid_url3 = 'http://intellitect.com/building-single-page-applications-spa-with-the-journey-framework'
        valid_url4 = 'http://intellitect.com/building-single-page-applications-spa-with-the-journey-framework/?utm_source=test&utm_medium=test&utm_campaign=test'

        invalid_url2 = 'http://intellitect.com?utm_source=test&utm_medium=test&utm_campaign=test'
        invalid_url4 = 'http://intellitect.com/building-single-page-applications-spa-with-the-journey-framework?utm_source=test&utm_medium=test&utm_campaign=test'

        assert Bitly.validate_url_for_creating(valid_url1)
        assert Bitly.validate_url_for_creating(valid_url2)
        assert Bitly.validate_url_for_creating(valid_url3)
        assert Bitly.validate_url_for_creating(valid_url4)
        assert Bitly.validate_url_for_creating(invalid_url2) is False
        assert Bitly.validate_url_for_creating(invalid_url4) is False

    def test_get_url(self):
        # don't want to use use global bitly because we set an invalid token
        bitly = Bitly()
        args = {'shortUrl': 'http://bit.ly/1PwCJwc'}
        self.assertRaises(LookupError, bitly.get_url, 'test', args)
        bitly.set_access_token("testToken")
        possible_url1 = bitly.api_address + "/v3/info?access_token=testToken&shortUrl=http%3A%2F%2Fbit.ly%2F1PwCJwc"
        possible_url2 = bitly.api_address + "/v3/info?shortUrl=http%3A%2F%2Fbit.ly%2F1PwCJwc&access_token=testToken"

        get_url = bitly.get_url('/v3/info', args)

        #print(get_url)
        # the order of arguments is not guaranteed
        assert get_url == possible_url1 or get_url == possible_url2

    def test_get_with_invalid_token(self):
        # don't want to use use global bitly because we set an invalid token
        bitly = Bitly()
        invalid_token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        bitly.set_access_token(invalid_token)
        validPath = '/v3/link/info'
        self.assertRaises(PermissionError, bitly.get, validPath, {'link': 'http://bit.ly/1PwCJwc'})

    def test_get_with_invalid_path(self):
        self.assertRaises(ConnectionError, TestBitly.globalBitly.get, '/invalidPath', {'link': 'http://bit.ly/1PwCJwc'})

    def test_get_target_url(self):
        target_url = TestBitly.globalBitly.get_target_url('http://bit.ly/1VeEV07')
        assert target_url == 'http://shanekercheval.me/why-some-businesses-fail?utm_source=twitterfeed&utm_medium=twitter'

        target_url = TestBitly.globalBitly.get_target_url('http://bit.ly/1VeESkZ')
        assert target_url == 'http://shanekercheval.me/why-some-businesses-fail?utm_source=twitterfeed&utm_medium=linkedin'

        target_url = TestBitly.globalBitly.get_target_url('http://bit.ly/1aSjH6j')
        assert target_url == 'http://shanekercheval.me/blog/monitor-the-web-with-google-alerts-and-slack/'


    def test_get_target_url_with_invalid_url(self):
        self.assertRaises(LookupError, TestBitly.globalBitly.get_target_url, 'http://bit.ly/qaqaqd1')

    def test_get_bitly_url(self):
        bitlyUrl = TestBitly.globalBitly.get_bitly_url('http://shanekercheval.me/why-some-businesses-fail?utm_source=twitterfeed&utm_medium=twitter')
        assert bitlyUrl == 'http://bit.ly/1VeEV07'

        bitlyUrl = TestBitly.globalBitly.get_bitly_url('http://shanekercheval.me/why-some-businesses-fail?utm_source=twitterfeed&utm_medium=linkedin')
        assert bitlyUrl == 'http://bit.ly/1VeESkZ'

        bitlyUrl = TestBitly.globalBitly.get_bitly_url('http://shanekercheval.me/blog/monitor-the-web-with-google-alerts-and-slack/')
        assert bitlyUrl == 'http://bit.ly/1aSjH6j'

    def test_get_bitly_url_with_invalid_url(self):
         self.assertRaises(LookupError, TestBitly.globalBitly.get_bitly_url, 'http://shanekercheval.me/url_doesnt_exist')

    def test_get_referrers(self):
        referrers = TestBitly.globalBitly.get_referrers('http://bit.ly/1aSjH6j')
        #print('--test_get_referrers--')
        total_clicks = 0
        for referrer in referrers:
            #print('-------')
            for name, value in referrer.items():
                if name == "clicks":
                    total_clicks += value
                #print("{}: {}".format(name, value))
                #print(value)
        total_clicks_from_api = TestBitly.globalBitly.get_total_clicks('http://bit.ly/1aSjH6j')
        #print('-----')
        #print('Total Click Count (referrers): {}; Total Click Count (API): {}'.format(total_clicks, total_clicks_from_api))
        assert total_clicks == total_clicks_from_api
        #print('--test_get_referrers--')

    def test_authenticate_http_basic_auth(self):
        with open('../../../settings/credentials.json') as json_file:
            json_data = json.load(json_file)
            assert 'bitly' in json_data
            assert 'username' in json_data['bitly']
            assert 'password' in json_data['bitly']
            assert 'access_token' in json_data['bitly']
            username = json_data['bitly']['username']
            password = json_data['bitly']['password']
            access_token = json_data['bitly']['access_token']

            tempBitly = Bitly()
            assert tempBitly.get_access_token() is None
            assert tempBitly.get_total_api_request_count() == 0
            tempBitly.authenticate_http_basic_auth(username=username, password=password)
            assert tempBitly.get_access_token() == access_token
            assert tempBitly.get_total_api_request_count() == 1


def tearDownModule():
    print("Total API Requests: '{}':".format(TestBitly.globalBitly.get_total_api_request_count()))

if __name__ == '__main__':
    unittest.main()
