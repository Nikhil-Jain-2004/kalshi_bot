import datetime

# TIME FUNCS #


def get_seconds_since_epoch(dt):
    dt_utc = dt.astimezone(datetime.timezone.utc)
    return int(dt_utc.timestamp())


def get_curr_time_seconds():
    curr_time = datetime.datetime.now()
    timestamp = curr_time.timestamp()
    curr_time_seconds = int(timestamp)
    return curr_time_seconds


def get_curr_time_milliseconds():
    curr_time = datetime.datetime.now()
    timestamp = curr_time.timestamp()
    curr_time_milliseconds = int(timestamp * 1000)
    return curr_time_milliseconds


def get_period_interval(string):
    match string:
        case "minute":
            return 1
        case "hour":
            return 60 * 1
        case "day":
            return 24 * 60 * 1
        case _:
            raise Exception("period_interval must be 'minute', 'hour', or 'day")