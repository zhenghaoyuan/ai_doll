from rest_framework.response import Response
from rest_framework import status
from .models import AwemeCustomUser
from django.contrib.auth.models import AnonymousUser
from .interfaces import IResponse, IResponseList, T
import inspect
from .AsyncLogging import AsyncLogger
from rest_framework.request import Request as DRFRequest
import logging
from typing import Dict, Any, Optional, Callable, Tuple, List, Union
from functools import wraps


VIEW_FUNCTION_TYPE = Callable[..., Any]


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
    code: int = 1,
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
    filtered_data = {k: v for k, v in data.items() if v is not None}
    rsp = IResponse(code=code, message=message, data=filtered_data)
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
    filtered_data = {k: v for k, v in data.items() if v is not None}
    rsp = IResponse(code=0, message=message, data=filtered_data)
    return Response(
        rsp.to_dict(),
        status=status.HTTP_200_OK,
    )


def generate_success_list_response(
    data_list: List[T],
    total: int,
    page: int,
    pagesize: int,
    message: str = "",
    user: AwemeCustomUser | AnonymousUser = AnonymousUser(),
    skip_logging: bool = False,
) -> Response:
    frame = inspect.currentframe()
    extra = {}
    if frame:
        frame = frame.f_back
        extra = {
            "caller_filename": frame.f_code.co_filename if frame else "missing",
            "caller_lineno": frame.f_lineno if frame else "missing",
            "caller_funcName": frame.f_code.co_name if frame else "missing",
        }
    if not skip_logging:
        logger.info(
            f"user={user.id}, message=List response, total={total}, page={page}, pagesize={pagesize}, count={len(data_list)}",
            extra=extra,
        )

    rsp = IResponseList(
        code=0,
        message=message,
        total=total,
        page=page,
        pagesize=pagesize,
        data=data_list,
    )

    return Response(
        rsp.to_dict(),
        status=status.HTTP_200_OK,
    )


def aweme_login_required(
    function: Optional[VIEW_FUNCTION_TYPE] = None,
) -> VIEW_FUNCTION_TYPE:
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """

    def decorator(view_func: VIEW_FUNCTION_TYPE) -> VIEW_FUNCTION_TYPE:
        @wraps(view_func)
        def _wrapper_view(request: DRFRequest, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            return generate_fail_generic_response(
                message="Incorrect authentication",
                data={},
                skip_logging=True,
            )

        return _wrapper_view

    if function:
        return decorator(function)
    return decorator
