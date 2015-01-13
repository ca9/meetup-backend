__author__ = 'aditya'

import endpoints

import data


app = endpoints.api_server([data.DataApi], )

