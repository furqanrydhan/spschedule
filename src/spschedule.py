#!/usr/bin/env python

import datetime
import dateutil.rrule
import dateutil.tz
import json
import time

import decorator
#import pymongo
#import pymongo.errors
#import pymongo.objectid
#import pymongo.son



if not hasattr(time, '_spschedule_configured'):
    time._spschedule_configured = False
    time._spschedule_persistence = None
    
    

FREQUENCIES = {
    'month':dateutil.rrule.MONTHLY,
    'week':dateutil.rrule.WEEKLY,
    'day':dateutil.rrule.DAILY,
    'hour':dateutil.rrule.HOURLY,
    'minute':dateutil.rrule.MINUTELY,
    'second':dateutil.rrule.SECONDLY,
    'once':None,
}



# Inverse operations to convert between UTC Unix timestamps (123456.789) and timezone aware UTC datetime objects
def to_datetime(timestamp_object):
    return datetime.datetime.fromtimestamp(timestamp_object, dateutil.tz.tzutc())
def to_timestamp(datetime_object):
    return time.mktime(datetime_object.timetuple()) + 1e-6*datetime_object.microsecond - time.timezone



# A scheduling rule
class _rule(object):
    def next(self, last=None):
        return NotImplemented

class _recurrence(_rule):
    freq = None
    interval = None
    def next(self, last=None):
        if last is None:
            return time.time()
        elif str(self.freq).lower() in ['once']:
            return None
        else:
            params = {
                'interval':int(self.interval),
            }
            if last is not None:
                params['dtstart'] = to_datetime(last)
            else:
                params['dtstart'] = to_datetime(time.time())
            generator = dateutil.rrule.rrule(FREQUENCIES[str(self.freq).lower()], **params)
            
            # Generate a future date.
            return to_timestamp(generator.after(to_datetime(time.time())))

class every_minute(_recurrence):
    freq = 'minute'
    interval = 1

class every_hour(_recurrence):
    freq = 'hour'
    interval = 1

class every_day(_recurrence):
    freq = 'day'
    interval = 1



# Persistence objects
class _persistence(object):
    def register(self, rule, f, args, kwargs):
        return NotImplemented
    def loop(self):
        return NotImplemented

class memory_persistence(_persistence):
    _registrations = {}
    _schedules = {}
    def register(self, rule, f, args, kwargs):
        if f not in self._registrations:
            self._registrations[f] = (rule, args, kwargs)
            self._schedules[f] = self._registrations[f][0].next(last=None)
    def loop(self):
        try:
            assert(len(self._schedules.keys()) > 0)
        except AssertionError:
            return
        while True:
            next = min(self._schedules.values())
            print 'next job is scheduled for ' + str(next - time.time()) + ' seconds from now'
            if next > time.time():
                time.sleep(next - time.time())
            for f in self._schedules.keys()[:]:
                next = self._schedules[f]
                if next < time.time():
                    f(*self._registrations[f][1], **self._registrations[f][2])
                    self._schedules[f] = self._registrations[f][0].next(self._schedules[f])

#class mongo_persistence(_persistence):
#    def finish(self, batch_entry, result):
#        try:
#            schedule = self.schedule(batch_entry)
#        except:
#            schedule = None
#        self.database('messaging').command(pymongo.son.SON([
#            ('findandmodify', 'batches'),
#            ('query', {'_id': batch_entry['_id'], 'batch_status': 'processing'}),
#            ('update', {
#                '$set': {
#                    'batch_status': 'scheduled' if schedule is not None else 'inactive',
#                    'processing_schedule': schedule,
#                },
#                '$push': {
#                    'processing_completed': time.time(),
#                    'processing_result': result,
#                },
#            }),
#        ]))
#    def fail(self, batch_entry):
#        return self.finish(batch_entry, 'failed')
#    def succeed(self, batch_entry):
#        return self.finish(batch_entry, 'succeeded')
#    def loop(self):
#        while True:
#            # We have to atomically change the status so no other worker will start working on the same item.
#            try:
#                now = time.time()
#                try:
#                    batch_entry = self.database('messaging').command(pymongo.son.SON([
#                        ('findandmodify', 'batches'),
#                        ('query',{
#                            'batch_status': 'scheduled',
#                            # Enforce scheduled deliveries.
#                            # N.B. Only the last "$or" in the query will be binding.  For some reason.
#                            '$or':[
#                                {'processing_schedule': {'$lt': now}},
#                                {'processing_schedule': {'$exists': False}},
#                            ],
#                        }),
#                        ('update',{
#                            '$set':{
#                                'batch_status': 'processing',
#                                'delivery_recipient_ids': [],
#                            },
#                            '$push':{
#                                'processing_initiated':time.time(),
#                            },
#                            '$inc':{
#                                'batch_iteration': 1,
#                            },
#                        }),
#                        ('new', True),
#                    ]))['value']
#                except pymongo.errors.OperationFailure:
#                    # Mongo doesn't do callbacks, as far as I can tell.
#                    # Polling is possibly our only option if we continue
#                    # using a Mongo-driven queue.
#                    time.sleep(QUEUE_EMPTY_NICE)
#                    continue
#                except pymongo.errors.AutoReconnect:
#                    print 'no mongo'
#                    time.sleep(MONGO_DOWN_NICE)
#                    continue
#                try:
#                    self.process(batch_entry)
#                    self.succeed(batch_entry)
#                except:
#                    self.fail(batch_entry)
#                    raise



# Configure the scheduler
def configure(*args, **kwargs):
    time._spschedule_persistence = memory_persistence()
    time._spschedule_configured = True

def scheduler(*args, **kwargs):
    if not time._spschedule_configured:
        configure(*args, **kwargs)
    return time._spschedule_persistence

def loop():
    scheduler().loop()



# A decorator to schedule the decorated function/method according to the
# given rule
class _schedule(object):
    def __init__(self, rule):
        self._rule = rule
        self._registered = False
    def __call__(self, func):
        if not self._registered:
            scheduler().register(self._rule, func, [], {})
        else:
            return func()
    
# Convenience decorators to schedule the decorated function/method according
# to the implicit rule.
# Usage:
# import spschedule
# @spschedule.minutely()
# def foo():
#     print 'foo'
# spschedule.loop()
class interval(_schedule):
    def __init__(self, **kwargs):
        EQUIVALENCE = {
            'minute':60,
            'minutes':60,
            'hour':60*60,
            'hours':60*60,
            'day':24*60*60,
            'days':24*60*60,
            'week':7*24*60*60,
            'weeks':7*24*60*60,
        }
        rule = _recurrence()
        seconds = 0
        for kwarg in kwargs.keys():
            assert(kwarg.lower() in EQUIVALENCE)
            seconds += (int(kwargs[kwarg]) * EQUIVALENCE[kwarg.lower()])
        rule.freq = 'second'
        rule.interval = seconds
        _schedule.__init__(self, rule)

class minutely(_schedule):
    def __init__(self):
        schedule.__init__(self, every_minute())

class hourly(_schedule):
    def __init__(self):
        schedule.__init__(self, every_hour())

class daily(_schedule):
    def __init__(self):
        schedule.__init__(self, every_day())