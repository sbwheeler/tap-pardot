#!/usr/bin/env python3
import os
import singer
from singer import utils


class IDS(object):
    VISITOR_ACTIVITY = 'visitor_activity'
    PROSPECT = 'prospect'


stream_ids = [getattr(IDS, x) for x in dir(IDS)
              if not x.startswith('__')]

PK_FIELDS = {
    IDS.VISITOR_ACTIVITY: ['id'],
    IDS.PROSPECT: ['id'],
}


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schema(tap_stream_id):
    path = "schemas/{}.json".format(tap_stream_id)
    return utils.load_json(get_abs_path(path))

def get_stream_from_catalog(stream_id, catalog):
    streams = catalog['streams']
    for s in streams:
        if s['tap_stream_id'] == stream_id:
            return s


def load_and_write_schema(tap_stream_id, catalog):
    stream = get_stream_from_catalog(tap_stream_id, catalog)
    singer.write_schema(
        tap_stream_id, stream['schema'], PK_FIELDS[tap_stream_id])