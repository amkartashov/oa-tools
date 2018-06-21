#!/usr/bin/env python

import time

from poaupdater import openapi
from poaupdater.uConfig import Config

import poaupdater.uLogging
poaupdater.uLogging.log_to_console = False
poaupdater.uLogging.logfile = open('poaupdater.log', 'w')


class OaError(Exception):
    pass

class OaApi:

    api_sync_timeout = 30
    check_period = 5

    def __init__(self, host=None, port=None, user=None, password=None):
        if host or port or user or password:
            openapi.init(host=host, port=port, user=user, password=password, proto = 'http')
        else:
            openapi.initFromEnv(Config())
        self.api = openapi.OpenAPI()

    def api_async_call(self, methodname, **kwargs):
        """Run async api call

        :returns: (request_id, response)
        """
        #TODO lock api until commit
        method = getattr(self.api, methodname)
        request_id = self.api.beginRequest()
        result = method(**kwargs)
        self.api.commit()
        return request_id, result

    def api_async_call_wait(self, methodname, timeout=None, **kwargs):
        """Run async api call and wait till execution

        :returns: response from api call
        :raises OaError: in case of timeout or API call failure
        """
        timeout = timeout or self.api_sync_timeout
        start_time = time.time()
        request_id, result = self.api_async_call(methodname, **kwargs)
        while True:
            status = self.api.pem.getRequestStatus(request_id=request_id)
            if status['request_status'] == 0:
                return result
            elif status['request_status'] == 2:
                raise OaError("Failure while executing {0} with args {1}, status: {2}"
                    .format(methodname, kwargs, status))
            if time.time() - start_time > timeout:
                raise OaError("Timeout ({2}) while executing {0} with args {1}"
                    .format(methodname, kwargs, timeout))
            time.sleep(self.check_period)

    def api_getMethodSignature(self, method_name):
        method = getattr(self.api.server,'pem.getMethodSignature')
        return method({ 'method_name' : method_name }).get('signature', None)
