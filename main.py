__author__ = 'aditya'

import endpoints
from api import authentication, data

app = endpoints.api_server(
    [authentication.UserApi, data.DataApi],
)

