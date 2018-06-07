from datetime import datetime

from pypardot.client import PardotAPI

import singer

logger = singer.get_logger()


def _join(a, b):
    return a.rstrip("/") + "/" + b.lstrip("/")


class Client(object):
    def __init__(self, config):
        self.email = config.get('email')
        self.password = config.get('password')
        self.user_key = config.get('user_key')
        self.pardot_client = self._auth_pardot_client()
        self.now_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _auth_pardot_client(self):
        return PardotAPI(email=self.email,
                         password=self.password,
                         user_key=self.user_key)

    def get(self, stream, date, offset):
        # some records come from Pardot showing a created_at in the future,
        # we need to explicitly exclude these in our query
        stream_mapping = {
            'visitor_activity': self.pardot_client.visitoractivities,
            'prospect': self.pardot_client.prospects
        }
        if stream == 'visitor_activity':
            return stream_mapping[stream].query(created_after=date,
                                                created_before=self.now_string,
                                                offset=offset,
                                                sort_by='created_at',
                                                sort_order='descending')
        elif stream == 'prospect':
            return stream_mapping[stream].query(updated_after=date,
                                                updated_before=self.now_string,
                                                offset=offset,
                                                sort_by='updated_at',
                                                sort_order='descending')
