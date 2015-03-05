"""
On disk cache decorator
found here: http://chase-seibert.github.io/blog/2011/11/23/pythondjango-disk-based-caching-decorator.html

example:

@cache_disk(seconds = 900, cache_folder="/tmp"):
def get_netflix_favorites(account_id):
   ... do somthing really expensive
   return {
      "account_id": account_id,
      "data": {
           ... more stuff here
      }
   }

"""
import os
import hashlib
import time
import pickle
import logging

def cache_disk(seconds = 900, cache_folder="/tmp"):
    def doCache(f):
        def inner_function(*args, **kwargs):

            # calculate a cache key based on the decorated method signature
            key = hashlib.sha224(str(f.__module__) + str(f.__name__) + str(args) + str(kwargs)).hexdigest()
            filepath = os.path.join(cache_folder, key)

            # verify that the cached object exists and is less than $seconds old
            if os.path.exists(filepath):
                modified = os.path.getmtime(filepath)
                age_seconds = time.time() - modified
                if age_seconds < seconds:
                    logging.info('cache found - using %s'%filepath)
                    return pickle.load(open(filepath, "rb"))
                else:
                    logging.info('cache found - but too old')
            # call the decorated function...
            result = f(*args, **kwargs)

            # ... and save the cached object for next time
            pickle.dump(result, open(filepath, "wb"), pickle.HIGHEST_PROTOCOL)

            return result
        return inner_function
    return doCache

