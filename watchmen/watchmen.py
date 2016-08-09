# watchmen is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# watchmen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with watchmen.  If not, see <http://www.gnu.org/licenses/>.


'''
Created on Aug 8, 2016

author: jakeret
'''
from __future__ import print_function, division, absolute_import, unicode_literals

import threading
import psutil
import time
import sys
import os
import Queue
import functools

__all__ = ["watch"]

SLEEP_TIME = 0.2

class WatchmenException(Exception):
    pass


class Event(object):
    SUCCESS = "sucess"
    ERROR = "error"
    LIMIT = "limit"
    
    def __init__(self, event_type, value):
        self.type = event_type
        self.value = value
        

class Watcher(threading.Thread):
    
    def __init__(self, queue, pid, sleep_time=None):
        self.queue = queue
        
        if sleep_time is None:
            sleep_time = SLEEP_TIME
        self.sleep_time = sleep_time
        self.process = psutil.Process(pid)
            
        self._cancelled = False
        super(Watcher, self).__init__()

    def _active(self):
        return not self._cancelled and self.process.is_running()

    def run(self):
        try:
            while self._active():
                state = self.update_state()
                if state is not None:
                    self.queue.put(state)
                    self.cancel()
                    
                time.sleep(self.sleep_time)
        except psutil.NoSuchProcess:
            self.cancel()
        except psutil.AccessDenied:
            self.cancel()
            
    def cancel(self):
        self._cancelled = True

class MemoryWatcher(Watcher):
    
    def __init__(self, max_mem, queue, pid, sleep_time=None):
        super(MemoryWatcher, self).__init__(queue, pid, sleep_time)
        self.max_mem = max_mem
    
    def update_state(self):
        processes = self.process.children(recursive=True)
        processes.append(self.process)
        
        rss_mem=0
        for process in processes:
            rss_mem += process.memory_info()[0]
        
        rss_mem = rss_mem / 1024 / 1024
        if rss_mem > self.max_mem:
            return Event(Event.LIMIT, "Memory limit exceeded. RSS: {} MB".format(rss_mem))

class TimeWatcher(Watcher):
    
    def __init__(self, max_time, queue, pid, sleep_time=None):
        super(TimeWatcher, self).__init__(queue, pid, sleep_time)
        self.max_time = max_time
        self.start_time = None
    
    def update_state(self):
        if self.start_time is None:
            self.start_time = time.time()
            
        delta = time.time() - self.start_time
        if delta > self.max_time:
            return Event(Event.LIMIT, "Time limit exceeded")

class CallableWrapper(threading.Thread):
    
    def __init__(self, func, queue, *args, **kwargs):
        self.callable = func
        self.queue = queue
        self.args = args
        self.kwargs = kwargs
        self.exception = None
        super(CallableWrapper, self).__init__()
        
    def run(self):
        try:
            result = self.callable(*self.args, **self.kwargs)
            self.queue.put(Event(Event.SUCCESS, result))
        except Exception:
            exc_info = sys.exc_info()
            self.queue.put(Event(Event.ERROR, exc_info))
             
    def cancel(self):
        pass


def watch(original_function=None, max_mem=None, max_time=None, sample_rate=None):
    """
    Decorator to watch a function or method.  
    
    :param max_mem: (optional) maximal memory limit in MB
    :param max_time: (optional) maximal execution time in seconds
    :param sample_rate: (optional) Rate at which the process is being queried
    """

    def _decorate(function):

        @functools.wraps(function)
        def wrapped_function(*args, **kwargs):
            pid = os.getpid()
            queue = Queue.Queue()
            threads = [CallableWrapper(function, queue, *args, **kwargs)]
            
            if max_mem is not None:
                threads.append(MemoryWatcher(max_mem, queue, pid, sample_rate))
            if max_time is not None:
                threads.append(TimeWatcher(max_time, queue, pid, sample_rate))
            
            for t in threads[::-1]:
                t.start()
            
            event = queue.get()
            
            for t in threads:
                t.cancel()
            
            if event.type == Event.LIMIT:
                raise WatchmenException(event.value)
            
            if event.type == Event.ERROR:
                raise event.value
            
            return event.value

        return wrapped_function

    if original_function is not None:
        return _decorate(original_function)

    return _decorate
