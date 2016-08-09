=============================
Watchmen
=============================

Watchdog implementation to monitor functions or methods.

To watch a longrunning function you can do the following::

	import time
	import watchmen
	
	@watchmen.watch(max_time=1)
	def longrunning(t):
	    time.sleep(t)
	    
	longrunning(t=10)

After 1 second an exception is raised::

	watchmen.watchmen.WatchmenException: Time limit exceeded
	
	
If you want to watch the memory consumption of a function::

	@watchmen.watch(max_mem=100)
	def memory_hungry(s):
	    l = [i*j for i in range(s) for j in range(s)]
	    
	memory_hungry(s=10000)

After a while an exception is raised::

	watchmen.watchmen.WatchmenException: Memory limit exceeded. RSS: 152.09765625 MB

**watchmen** can also be used on instance methods::

	class Demo(object):
	    @watchmen.watch(max_mem=100)
	    def memory_hungry(self, s):
	        l = [i*j for i in range(s) for j in range(s)]
	    
	Demo().memory_hungry(s=10000)
