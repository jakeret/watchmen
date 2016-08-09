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

"""
Tests for `watchmen` module.
"""
from __future__ import print_function, division, absolute_import, unicode_literals

import pytest
from watchmen import watch
import time
from watchmen.watchmen import WatchmenException


class TestWatchmen(object):

    def test_plain_callable(self):
        
        def fkt():
            pass
        watched_fkt = watch(fkt)
        assert watched_fkt() is None

    def test_returning_callbable(self):
        def fkt():
            return 1
        watched_fkt = watch(fkt)
        assert watched_fkt() == 1

    def test_args_callbable(self):
        def fkt(a):
            return a
        watched_fkt = watch(fkt)
        
        v = "a"
        assert watched_fkt(v) == v
        
    def test_kwargs_callbable(self):
        def fkt(a):
            return a
        watched_fkt = watch(fkt)
        
        v = "a"
        assert watched_fkt(a=v) == v

    def test_args_kwargs_callbable(self):
        def fkt(a, b):
            return a, b
        watched_fkt = watch(fkt)
        
        v = "a"
        assert watched_fkt(v, b=v) == (v,v)
        
    def test_timeout(self):
        def fkt():
            time.sleep(20)
        watched_fkt = watch(max_time=1)(fkt)
        
        with pytest.raises(WatchmenException):
            watched_fkt()

    def test_args_timeout(self):
        def fkt(t):
            time.sleep(t)
        watched_fkt = watch(max_time=1)(fkt)
        
        with pytest.raises(WatchmenException):
            watched_fkt(2)

    def test_kwargs_timeout(self):
        def fkt(t):
            time.sleep(t)
        watched_fkt = watch(max_time=1)(fkt)
        
        with pytest.raises(WatchmenException):
            watched_fkt(t=2)

    def test_memlimit(self):
        def fkt():
            l = [i*j for i in range(10000) for j in range(10000)]
            time.sleep(10)
        watched_fkt = watch(max_mem=100)(fkt)
        
        with pytest.raises(WatchmenException):
            watched_fkt()

