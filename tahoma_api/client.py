""" Python wrapper for the Tahoma API """
import aiohttp

import asyncio
import logging
import time
import hashlib
import math
import random
import json

from .exceptions import *

API_URL = 'https://tahomalink.com/enduser-mobile-web/enduserAPI/'  # /doc for API doc

class TahomaClient(object):
    """ Interface class for the Tahoma API """

    def __init__(self, username, password):
        """
        Constructor

        :param username: the username for Tahomalink.com
        :param password: the password for Tahomalink.com
        """

        self.username = username
        self.password = password

        self.__roles = []

    async def login(self):
        
        payload = {
            'userId': self.username,
            'userPassword': self.password
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL + 'login', data=payload) as response:

                result = await response.json()

                # 401
                # {'errorCode': 'AUTHENTICATION_ERROR', 'error': 'Bad credentials'}

                # 401
                # {'errorCode': 'AUTHENTICATION_ERROR', 'error': 'Too many requests, try again later : login with xxx@xxx.tld'}
                # TODO Add retry logic on too many requests + for debug, log requests + timespans

                # 200
                # {'success': True, 'roles': [{'name': 'ENDUSER'}]}
                if (response.status is 200):
                    if result['success'] == True:
                        self.__roles = result['roles']
                        self.__cookies = response.cookies

                        return True

                print(response.status)
                print(result)

    async def get_devices(self):
        
        cookies = self.__cookies

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + 'setup/devices', cookies=cookies) as response:

                print(response.status)
                print(response)
                
                result = await response.json()

                print(result)
                # 401
                # {'errorCode': 'AUTHENTICATION_ERROR', 'error': 'Bad credentials'}

                # {'success': True, 'roles': [{'name': 'ENDUSER'}]}
                if (response.status is 200):
                    if result["success"] == True:
                        print(result)

                # TODO Save cookies

    async def get_states(self):
        
        cookies = self.__cookies

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + 'setup/devices/states', cookies=cookies) as response:

                print(response.status)                
                result = await response.json()

                print(result)
   


    


