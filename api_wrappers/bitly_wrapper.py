import requests
import logging
import urllib.parse


class Bitly:
    __access_token = None
    __total_api_request_count = 0

    def __init__(self, access_token=None):
        self.api_address = "https://api-ssl.bitly.com"
        self.__access_token = access_token

    def get_target_url(self, bitly):
        args = {'shortUrl': bitly}
        json = self.get('/v3/expand', args)
        if 'error' in json['data']['expand'][0]:
            raise LookupError("(get_target_url) error: '{}'"
                              .format(json['data']['expand'][0]['error']))
        return json['data']['expand'][0]['long_url']

    def get_bitly_url(self, target):
        args = {'url': target}
        json = self.get('/v3/user/link_lookup', args)
        if 'error' in json['data']['link_lookup'][0]:
            raise LookupError("(get_target_url) error: '{}'"
                              .format(json['data']['link_lookup'][0]['error']))
        return json['data']['link_lookup'][0]['link']

    def get_referrers(self, bitly):
        """takes a short bitly, returns a dictionary of referrers"""
        args = {'link': bitly}
        json = self.get('/v3/link/referring_domains', args)
        return json['data']['referring_domains']

    def create_bitly(self, long_url):
        if not Bitly.validate_url_for_creating(long_url):
            raise SyntaxError('Unable to validate: {}'.format(long_url))
        args = {'longUrl': long_url}
        json = self.get('/v3/user/link_save', args)
        return json['data']['link_save']['link']

    def create_or_get_bitly(self, long_url):
        if not Bitly.validate_url_for_creating(long_url):
            raise SyntaxError('Unable to validate: {}'.format(long_url))
        args = {'longUrl': long_url}
        json = self.get('/v3/user/link_save', args, ignore_json_status_code=304)
        return json['data']['link_save']['link']

    @staticmethod
    def validate_url_for_creating(url):
        """
        http://dev.bitly.com/links.html#v3_user_link_save
        'Long URLs must have a slash between the domain and the path component. For example, http://example.com?query=parameter is invalid, and instead should be formatted as http://example.com/?query=parameter'
        :return:
        """
        parsed = urllib.parse.urlparse(url)
        if parsed[4] == '':
            return True

        #otherwise, params exist
        if parsed[3] != '': # not sure what [3] this is, so lets raise exception for now, so if there ever is one, we can figure it out
            raise SystemError('not sure what parsed[3] is: {}'.format(parsed[3]))

        if parsed[2] != '':
            # check for '/' at end
            return parsed[2][-1:] == '/'

        if parsed[1] != '':
            # check for '/' at end
            return parsed[1][-1:] == '/'

        raise SystemError("Can't validate url for creating bitly: {}".format(url))

    def get_total_clicks(self, bitly):
        """takes a short bitly, returns a dictionary of referrers"""
        args = {'link': bitly, 'rollup': 'true', 'units': "-1"}
        json = self.get('/v3/link/clicks', args)
        return json['data']['link_clicks']

    def get(self, path, arguments, ignore_json_status_code=None):
        """generic method to handle API get requests"""
        r = requests.get(self.get_url(path, arguments))
        self.__total_api_request_count += 1
        if r.ok is not True:
            raise ConnectionError('(get)status_code: "{}"'.format(r.status_code))

        json = r.json()
        if json['status_code'] != 200:
            if json['status_code'] == ignore_json_status_code:
                return json
            raise PermissionError(
                '(get)json-status_code: "{}";json-status_txt: "{}"'
                .format(json['status_code'], json['status_txt']))
        return json

    def get_url(self, path, arguments):
        """arguments is a dictionary"""
        if self.__access_token is None:
            raise LookupError("no access token, login or set token")

        arguments['access_token'] = self.__access_token
        url = "{}{}?{}".format(self.api_address,
                               path,
                               urllib.parse.urlencode(arguments))
        return url

    def authenticate_http_basic_auth(self, username, password):
        """uses HTTP Basic Auth - http://dev.bitly.com/authentication.html"""

        if self.__access_token is None:
            logging.debug("logging in using HTTP Basic Auth")

            from requests.auth import HTTPBasicAuth
            data = {'format': 'json'}
            r = requests.post('https://api-ssl.bitly.com/oauth/access_token',
                              data=data,
                              auth=HTTPBasicAuth(username, password))

            self.__total_api_request_count += 1

            if r.ok is not True:
                raise ConnectionError("status_code: '{}'"
                                      .format(r.status_code))
            self.__access_token = r.content.decode("utf-8")

    def set_access_token(self, access_token):
        self.__access_token = access_token

    def get_access_token(self):
        return self.__access_token

    def get_total_api_request_count(self):
        return self.__total_api_request_count
