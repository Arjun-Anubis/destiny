import threading
from destiny.header import log

class ExThread( threading.Thread ):
    def run_x( *args, **kwargs ):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception as e:
            raise e


class RaisingThread(threading.Thread):
    def run(self):
        self._exc = None
        try:
            super().run()
        except Exception as e:
            self._exc = e
            log.warning( "There was an excption" )

    def join(self, timeout=None):
        super().join(timeout=timeout)
        if self._exc:
            raise self._exc
