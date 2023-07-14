import functools
import time

import requests
from flask import request


def reliable_query(
    failure_message="Sorry, our servers are currently overloaded",
    user_email="ishaan@berri.ai",
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Record start time
                start_time = time.time()
                request_args = request.args.to_dict()  # if this is flask

                # log incoming request
                # get a uuid for it
                req_uuid = write_log(request_args, user_email)
            except Exception as e:
                print(f"failed creating log{e}")

            try:
                result = func(*args, **kwargs)

                try:
                    # Calculate response time
                    response_time = time.time() - start_time

                    update_log(req_uuid, result, response_time)
                except BaseException:
                    print("failed updating log")
            except Exception as e:
                try:
                    update_log(req_uuid, "", "", error=e, error_type=str(type(e)))
                except BaseException:
                    print("failed updating log with error")
                result = failure_message
            return result

        return wrapper

    return decorator


# Call write_log endpoint
def write_log(kwargs, user_email):
    # Replace <your_domain> with the actual domain or IP address
    url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/write_log"
    params = {
        "user_email": user_email,
    }

    # data = {
    #     'kwargs': json.dumps(kwargs),
    # }

    response = requests.post(url, params=params, json=kwargs)

    uuid = response.text

    # req_uuid - response.json('uuid')
    return uuid


# Call update_log endpoint
def update_log(req_uuid, result, response_time=0, error="", error_type=""):
    # Replace <your_domain> with the actual domain or IP address
    url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/update_log"
    params = {
        "req_uuid": req_uuid,
        "result": result,
        "response_time": response_time,
        "error": error,
        "error_type": error_type,
    }

    response = requests.post(url, params=params)

    return response
