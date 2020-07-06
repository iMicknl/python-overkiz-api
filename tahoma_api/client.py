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


        self._devices = None


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
                # {'errorCode': 'AUTHENTICATION_ERROR', 'error': 'Your setup cannot be accessed through this application'}
                if response.status == 401:
                    if result['errorCode'] == 'AUTHENTICATION_ERROR':

                        if 'Too many requests' in result['error']:
                            print(result['error'])

                        if 'Your setup cannot be accessed through this application' in result['error']:
                            print(result['error'])

                        if 'Bad credentials' in result['error']:
                            print(result['error'])

                        print(result['error'])

                        return False # todo throw error
                   
                # 401
                # {'errorCode': 'AUTHENTICATION_ERROR', 'error': 'Too many requests, try again later : login with xxx@xxx.tld'}
                # TODO Add retry logic on too many requests + for debug, log requests + timespans
   
                # 200
                # {'success': True, 'roles': [{'name': 'ENDUSER'}]}
                if response.status == 200:
                    if result['success'] == True:
                        self.__roles = result['roles']
                        self.__cookies = response.cookies

                        return True

                # Temp fallbacks
                print(response.status)
                print(result)

    async def get_devices(self, refresh=False):

        if self._devices is None or refresh == True:

            cookies = self.__cookies

            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL + 'setup/devices', cookies=cookies) as response:

                    result = await response.json()

                    if (response.status is 200):
                        self._devices = result

                        return result
                    
                    # TODO add retry logic for unauthorized?

                    else:
                        return []
                    # TODO Save cookies