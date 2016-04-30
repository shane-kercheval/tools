# tools
A collection of tools to help get shit done.

# credentials
- credentials are stored in a json file in a private git repository (settings/credentials.json)
    - ensure the file exists and in the correct relative loction
    - see example.json for expected key/values
    

# Google Analytics Wrapper
- client_secrets.json is needed in the tools/api_wrappers directory. 
    - This file is added added to the .gitignore so it is not uploaded.
    - note to self: I stored my copy in settings/ repo
- getting started:
    - https://developers.google.com/api-client-library/python/start/get_started
    - pip install --upgrade google-api-python-client
    - https://console.developers.google.com/apis/     configure OAuth2.0 and download json for 'client_secrets.json'

