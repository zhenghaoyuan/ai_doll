from rest_framework.response import Response
from rest_framework import status
from .models import AwemeCustomUser
from django.contrib.auth.models import AnonymousUser
from .interfaces import IResponse, IResponseList
import inspect
from .AsyncLogging import AsyncLogger
import logging
from typing import Any


class CustomLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    def process(self, msg, kwargs):
        # Get the caller's stack frame, going two frames back to find the caller
        frame = inspect.currentframe()
        if not frame:
            return {}
        frame = frame.f_back
        if not frame:
            return {}
        frame = frame.f_back
        if not frame:
            return {}
        # Set the extra attributes including filename, line number, and function name
        kwargs["extra"] = {
            "filename": frame.f_code.co_filename,
            "lineno": frame.f_lineno,
            "funcName": frame.f_code.co_name,
        }
        return msg, kwargs


logging.setLoggerClass(AsyncLogger)
logger = logging.getLogger(__name__)
custom_logger = CustomLoggerAdapter(logger, {})


def generate_fail_generic_response(
    message: str,
    data: dict[str, Any] = {},
    user: AwemeCustomUser | AnonymousUser = AnonymousUser(),
    skip_logging: bool = False,
) -> Response:
    frame = inspect.currentframe()
    extra = {}
    if frame:
        frame = frame.f_back
        extra = {
            "caller_filename": frame and frame.f_code.co_filename or "missing",
            "caller_lineno": frame and frame.f_lineno or "missing",
            "caller_funcName": frame and frame.f_code.co_name or "missing",
        }
    if not skip_logging:
        logger.warn(f"user={user.id}, message={message}, data={data}", extra=extra)
    data["message"] = message
    filtered_data = {k: v for k, v in data.items() if v is not None}
    rsp = IResponse(data=filtered_data)
    return Response(
        rsp.to_dict(),
        status=status.HTTP_400_BAD_REQUEST,
    )


def generate_success_generic_response(
    message: str,
    data: dict[str, Any] = {},
    user: AwemeCustomUser | AnonymousUser = AnonymousUser(),
    skip_logging: bool = False,
) -> Response:
    frame = inspect.currentframe()
    extra = {}
    if frame:
        frame = frame.f_back
        extra = {
            "caller_filename": frame and frame.f_code.co_filename or "missing",
            "caller_lineno": frame and frame.f_lineno or "missing",
            "caller_funcName": frame and frame.f_code.co_name or "missing",
        }
    if not skip_logging:
        logger.info(f"user={user.id}, message={message}, data={data}", extra=extra)
    data["message"] = message
    filtered_data = {k: v for k, v in data.items() if v is not None}
    rsp = IResponse(data=filtered_data)
    return Response(
        rsp.to_dict(),
        status=status.HTTP_200_OK,
    )
