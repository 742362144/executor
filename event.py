'''
Copyright (2019, ) Institute of Software, Chinese Academy of Sciences

@author: wuyuewen@otcaix.iscas.ac.cn
@author: wuheng@otcaix.iscas.ac.cn
'''
import datetime
import random

from dateutil.tz import gettz

'''
Import python libs
'''

'''
Import third party libs
'''
from kubernetes import client

EVENT_TYPE_NORMAL = 'Normal'
EVENT_TYPE_WARNING = 'Warning'
STATUS_DOING_SUCCESSS = 'Doing(Success)'
STATUS_DONE_SUCCESSS = 'Done(Success)'
STATUS_DONE_ERROR = 'Done(Error)'


class Event:
    def __init__(self, kind, name, reporter, operation):
        self.kind = kind
        self.name = name
        self.event_uuid = randomUUID()
        # self.event_type = event_type
        # self.event_status = event_status
        self.reporter = reporter
        self.operation = operation
        self.start_event_time = event_datetime()
        self.finish_event_time = event_datetime()

    def event(self, event_type, event_status):
        message = 'type:%s, name:%s, operation:%s, event_status:%s, reporter:%s, eventId:%s, duration:%f' \
                  % (self.kind, self.name, self.operation, event_status, self.reporter, self.event_uuid,
                     (self.finish_event_time - self.start_event_time).total_seconds())
        return client.V1Event(first_timestamp=self.start_event_time, last_timestamp=self.finish_event_time,
                              metadata=self.metadata(self.event_uuid), involved_object=self.object(event_type),
                              message=message, type=event_type)

    def register(self):
        body = self.event(EVENT_TYPE_NORMAL, STATUS_DOING_SUCCESSS)
        client.CoreV1Api().replace_namespaced_event(self.event_uuid, 'default', body, pretty='true')

    def error(self):
        self.finish_event_time = event_datetime()
        body = self.event(EVENT_TYPE_NORMAL, STATUS_DONE_ERROR)
        client.CoreV1Api().replace_namespaced_event(self.event_uuid, 'default', body, pretty='true')

    def success(self):
        self.finish_event_time = event_datetime()
        body = self.event(EVENT_TYPE_NORMAL, STATUS_DONE_SUCCESSS)
        client.CoreV1Api().replace_namespaced_event(self.event_uuid, 'default', body, pretty='true')

    def metadata(self, uuid):
        return client.V1ObjectMeta(name=uuid, namespace='default')

    def object(self, name):
        return client.V1ObjectReference(name=name, kind=self.kind, namespace='default')


def event_datetime():
    time_zone = gettz('Asia/Shanghai')
    return datetime.datetime.now(tz=time_zone)


def randomUUID():
    u = [random.randint(0, 255) for ignore in range(0, 16)]
    u[6] = (u[6] & 0x0F) | (4 << 4)
    u[8] = (u[8] & 0x3F) | (2 << 6)
    return "-".join(["%02x" * 4, "%02x" * 2, "%02x" * 2, "%02x" * 2,
                     "%02x" * 6]) % tuple(u)
