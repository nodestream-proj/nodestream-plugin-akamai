from functools import wraps
from time import sleep


def attempt(times=None, backoff=None):
    """
    Attempts to call a function several times with a linear backoff
    Note, that this is generally not needed unless you want an operation to be
    be repeated several times inside of the same execution. Generally if an exception is
    thrown, the errorred request will be retried by lambda.
    """
    times = 3 if times is None else times
    backoff = 1 if backoff is None else backoff

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            should_continue = True
            current_backoff = attempts_made = 0
            last_error = None

            while should_continue:
                attempts_made += 1
                current_backoff += backoff
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    sleep(current_backoff)
                    should_continue = attempts_made != times
            raise last_error

        return decorated

    return decorator
