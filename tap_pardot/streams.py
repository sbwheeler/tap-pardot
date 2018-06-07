import json
from datetime import datetime

import singer

from .schemas import IDS

logger = singer.get_logger()


def metrics(tap_stream_id, records):
    with singer.metrics.record_counter(tap_stream_id) as counter:
        counter.increment(len(records))


def write_records(tap_stream_id, records):
    singer.write_records(tap_stream_id, records)
    metrics(tap_stream_id, records)


class BOOK(object):
    VISITOR_ACTIVITY = [IDS.VISITOR_ACTIVITY, 'created_at']

    @classmethod
    def return_bookmark_path(cls, stream):
        return getattr(cls, stream.upper())

    @classmethod
    def get_incremental_syncs(cls):
        syncs = []
        for k, v in cls.__dict__.items():
            if not k.startswith("__") and not isinstance(v, classmethod):
                if len(v) > 1:
                    syncs.append(k)

        return syncs

    @classmethod
    def get_full_syncs(cls):
        syncs = []
        for k, v in cls.__dict__.items():
            if not k.startswith("__") and not isinstance(v, classmethod):
                if len(v) == 1:
                    syncs.append(k)

        return syncs


def sync(context):
    # do full syncs first as they are used later
    for stream in context.selected_stream_ids:
        if stream.upper() in BOOK.get_full_syncs():
            call_stream_full(context, stream)

    for stream in context.selected_stream_ids:
        if stream.upper() in BOOK.get_incremental_syncs():
            bk = call_stream_incremental(context, stream)
            save_state(context, stream, bk)


def call_stream_full(context, stream):
    response = context.client.GET(stream='campaigns')
    records_to_write = json.loads(response.content)
    write_records(stream, records_to_write)

    context.save_campaigns_meta(records_to_write)


def call_stream_incremental(context, stream):
    context.update_start_date_bookmark(BOOK.return_bookmark_path(stream))
    last_updated = context.get_bookmark(BOOK.return_bookmark_path(stream))

    # TODO: make sure date field is properly configured
    # TODO: get proper date off of last_updated

    offset = 0
    total_records = 1
    most_recent_record_date = None

    while total_records > offset:
        response = context.client.get(stream, last_updated, offset)

        if offset == 0:
            logger.info('{ts} - querying {stream} since: {since} for {total}'
                        ' total results'.format(
                            ts=datetime.now(),
                            stream=stream,
                            since=last_updated,
                            total=response['total_results']
                        ))
            total_records = response['total_results']
            if total_records == 0:
                return

            # results ordered by date ascending
            # most_recent_record_date = format_record_to_state_date(
                # response[stream][0]['created_at'])
            most_recent_record_date = response[stream][0]['created_at']

        data = response[stream]
        write_records(stream, data)

        # batch size of 200 via pardot API
        offset = offset + 200

    return most_recent_record_date


def format_record_to_state_date(datestring):
    return datestring.replace(' ', 'T') + '+00:00'

def save_state(context, stream, bk):
    context.set_bookmark(BOOK.return_bookmark_path(stream), bk)
    context.write_state()
