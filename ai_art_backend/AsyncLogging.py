import concurrent.futures
import logging
import inspect
from typing import Dict, Any


def custom_log_record_factory(old_factory, *args, **kwargs):
    record = old_factory(*args, **kwargs)
    extra = kwargs.get("extra", {})
    for key, value in extra.items():
        setattr(record, key, value)
    return record


class AsyncLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def _capture_default_caller_context(
        self,
    ) -> Dict[str, Any]:
        # Capture the stack of the caller to the logging function
        frame = inspect.currentframe()
        if not frame:
            return {}
        frame = frame.f_back
        if not frame:
            return {}
        frame = frame.f_back
        if not frame:
            return {}
        return {
            "caller_filename": frame.f_code.co_filename or "missing",
            "caller_lineno": frame.f_lineno or "missing",
            "caller_funcName": frame.f_code.co_name or "missing",
        }

    def info(self, msg, *args, **kwargs):
        default_caller_context = self._capture_default_caller_context()
        kwargs["extra"] = {
            **default_caller_context,
            **kwargs.get("extra", {}),
        }  # override by original extra params
        self.executor.submit(super(AsyncLogger, self).info, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        default_caller_context = self._capture_default_caller_context()
        kwargs["extra"] = {
            **default_caller_context,
            **kwargs.get("extra", {}),
        }  # override by original extra params
        self.executor.submit(super(AsyncLogger, self).debug, msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        default_caller_context = self._capture_default_caller_context()
        kwargs["extra"] = {
            **default_caller_context,
            **kwargs.get("extra", {}),
        }  # override by original extra params
        self.executor.submit(super(AsyncLogger, self).warn, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        default_caller_context = self._capture_default_caller_context()
        kwargs["extra"] = {
            **default_caller_context,
            **kwargs.get("extra", {}),
        }  # override by original extra params
        self.executor.submit(super(AsyncLogger, self).error, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        default_caller_context = self._capture_default_caller_context()
        kwargs["extra"] = {
            **default_caller_context,
            **kwargs.get("extra", {}),
        }  # override by original extra params
        self.executor.submit(super(AsyncLogger, self).critical, msg, *args, **kwargs)
