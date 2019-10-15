'''
Copyright (2019, ) Institute of Software, Chinese Academy of Sciences

@author: wuyuewen@otcaix.iscas.ac.cn
@author: wuheng@otcaix.iscas.ac.cn
'''
import datetime
import socket

from dateutil.tz import gettz

'''
Import python libs
'''
import ConfigParser
import os
import string
import sys
import time
from threading import Thread

'''
Import third party libs
'''
from kubernetes import client, watch
from kubernetes.client import V1DeleteOptions
from libvirt import libvirtError

'''
Import local libs
'''
from utils.libvirt_util import destroy, \
    create, is_vm_active, is_vm_exists
from utils import logger, constants
from utils.utils import ExecuteException, \
    report_failure, randomUUID, now_to_datetime, get_hostname_in_lower_case, UserDefinedEvent

logger = logger.set_logger(os.path.basename(__file__), constants.VIRTCTL_DEBUG_LOG)


class Executor():

    def __init__(self, policy, invoke_cmd, query_cmd):
        self.policy = policy
        self.invoke_cmd = invoke_cmd
        self.query_cmd = query_cmd

    def execute(self):

        if not self.invoke_cmd or not self.query_cmd:
            logger.debug('Missing the command.')
            return result('', 'Error', 'Missing the command.')

        invoke_process = subprocess.Popen(self.invoke_cmd, shell=True,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if invoke_process.returncode == 0:
            return result(self.invoke_cmd, 'Error', self.error_msg(invoke_process.stderr))

        query_process = subprocess.Popen(self.query_cmd, shell=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if query_process.returncode == 0:
            return result(self.query_cmd, 'Error', self.error_msg(invoke_process.stderr))
        else:
            return result(self.query_cmd, 'Success', self.normal_out(invoke_process.stdout))

    def normal_out(self, stdout):
        try:
            if self.query_cmd == 'default':
                stdout = stdout.readlines()
                for line in enumerate(stdout):
                    if not str.strip(line):
                        continue
                    line = str.strip(line)
                    kv = line.replace(':', '').split()
                    result[kv[0].lower()] = kv[1]
                return result
            else:
                process = subprocess.Popen(self.query_cmd, shell=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if process.returncode == 0:
                    return result(self.invoke_cmd, 'Error', self.error_msg(process.stderr))
                else:
                    return result(self.invoke_cmd, 'Success', self.normal_out(process.stdout))
        except:
            return "Success without any output"
        finally:
            stdout.close()

    def error_msg(self, stderr):
        try:
            std_err = stderr.readlines()
            error_msg = ''
            for line in enumerate(std_err):
                if not str.strip(line):
                    continue
                else:
                    error_msg += str.strip(line).replace(':', '')
            return str.strip(error_msg)
        except:
            return "Unknown reason"
        finally:
            stderr.close()


def result(cmd, status, data):
    err = {}
    err['command'] = cmd
    err['status'] = status
    err['data'] = data
    return err

