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


class Watcher(object):

    def __init__(self, group, version, plural, kind, metadataInfo, commandInfo):
        self.group = group
        self.version = version
        self.plural = plural
        self.kind = kind
        self.metadataInfo = metadataInfo
        self.commandInfo = commandInfo
        logger.info("Start " + kind + " watcher successfully.")

    def start(self, ):
        kwargs = {}
        kwargs['label_selector'] = label_selector()
        kwargs['timeout_seconds'] = 31536000
        kwargs['watch'] = True

        w = watch.Watch()
        for jsondict in w.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                 group=self.group, version=self.version, plural=self.plural, **kwargs):
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            if operation_type == 'ADDED':
                self.add()
            elif operation_type == 'MODIFIED':
                self.modify()
            elif operation_type == 'DELETED':
                self.delete()


    def add(self):
        # convertor
        # registerEvent
        # executor
        pass
        # updateEvent

    def modify(self):
        # convertor
        # registerEvent
        # executor
        pass
        # updateEvent

    def append(self):
        # convertor
        # registerEvent
        # executor
        pass
        # updateEvent

    def delete(self):
        # convertor
        # registerEvent
        # executor
        pass
        # updateEvent

    def report(self, name, body):
        try:
            client.CustomObjectsApi().replace_namespaced_custom_object(
                group=self.group, version=self.version, plural=self.plural, namespace='default', name=name, body=body)
        except:
            logger.error('Error', 'Write result to kube-apiserver failure: %s' % body)



def label_selector():
    return socket.gethostname().lower()


def event_uuid(json):
    metadata = json['raw_object'].get('metadata')
    labels = metadata.get('labels')
    return labels.get('eventId') if labels.get('eventId') else '-1'


def event_datetime():
    time_zone = gettz('Asia/Shanghai')
    return datetime.datetime.now(tz=time_zone)




def vMWatcher(group=GROUP_VM, version=VERSION_VM, plural=PLURAL_VM):

    for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                   group=group, version=version, plural=plural, **kwargs):
        try:
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            metadata_name = getMetadataName(jsondict)
            logger.debug('metadata name: %s' % metadata_name)
            the_cmd_key = _getCmdKey(jsondict)
            logger.debug('cmd key is: %s' % the_cmd_key)
        except:
            logger.warning('Oops! ', exc_info=1)
        try:
            if the_cmd_key and operation_type != 'DELETED':
                #                 _vm_priori_step(the_cmd_key, jsondict)
                (jsondict, operations_queue) \
                    = _vm_prepare_step(the_cmd_key, jsondict, metadata_name)
                jsondict = forceUsingMetadataName(metadata_name, the_cmd_key, jsondict)
                cmd = unpackCmdFromJson(jsondict, the_cmd_key)
                involved_object_name = metadata_name
                involved_object_kind = 'VirtualMachine'
                event_metadata_name = randomUUID()
                event_type = 'Normal'
                status = 'Doing(Success)'
                reporter = 'virtctl'
                event_id = _getEventId(jsondict)
                time_now = now_to_datetime()
                time_start = time_now
                time_end = time_now
                message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                (time_end - time_start).total_seconds())
                event = UserDefinedEvent(event_metadata_name, time_start, time_end, involved_object_name,
                                         involved_object_kind, message, the_cmd_key, event_type)
                try:
                    event.registerKubernetesEvent()
                except:
                    logger.error('Oops! ', exc_info=1)
                #             jsondict = _injectEventIntoLifecycle(jsondict, event.to_dict())
                #             body = jsondict['raw_object']
                #             jsondict1 = client.CustomObjectsApi().get_namespaced_custom_object(group=group, version=version, namespace='default', plural=plural, name=metadata_name)
                #             logger.debug(jsondict1)
                #             logger.debug(body)
                #             try:
                #                 client.CustomObjectsApi().replace_namespaced_custom_object(group=group, version=version, namespace='default', plural=plural, name=metadata_name, body=body)
                #             except:
                #                 logger.warning('Oops! ', exc_info=1)
                try:
                    #             print(jsondict)
                    if operation_type == 'ADDED':
                        if _isInstallVMFromISO(the_cmd_key) or _isInstallVMFromImage(the_cmd_key):
                            if cmd:
                                runCmd(cmd)
                            if is_vm_exists(metadata_name) and not is_vm_active(metadata_name):
                                create(metadata_name)
                            time.sleep(2)
                        else:
                            if cmd:
                                runCmd(cmd)
                        '''
                        Run operations
                        '''
                        if operations_queue:
                            for operation in operations_queue:
                                logger.debug(operation)
                                if operation.find('kubeovn-adm unbind-swport') != -1:
                                    try:
                                        runCmd(operation)
                                    except:
                                        pass
                                else:
                                    runCmd(operation)
                                time.sleep(1)
                    elif operation_type == 'MODIFIED':
                        #                         if not is_vm_exists(metadata_name):
                        #                             raise ExecuteException('VirtctlError', '404, Not Found. VM %s not exists.' % metadata_name)
                        if _isDeleteVM(the_cmd_key):
                            if is_vm_active(metadata_name):
                                destroy(metadata_name)
                                time.sleep(1)
                        try:
                            runCmd(cmd)
                        except Exception, e:
                            if _isDeleteVM(the_cmd_key) and not is_vm_exists(metadata_name):
                                logger.warning("***VM %s not exists, delete it from virtlet" % metadata_name)
                                deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                            else:
                                raise e

                        #                                 file_path = '%s/%s-*' % (DEFAULT_DEVICE_DIR, metadata_name)
                        #                                 mvNICXmlToTmpDir(file_path)
                        # add support python file real path to exec
                        '''
                        Run operations
                        '''
                        if operations_queue:
                            for operation in operations_queue:
                                logger.debug(operation)
                                runCmd(operation)
                                time.sleep(1)
                    #                     elif operation_type == 'DELETED':
                    #                         logger.debug('Delete custom object by client.')
                    #                     if is_vm_exists(metadata_name):
                    #                         if is_vm_active(metadata_name):
                    #                             destroy(metadata_name)
                    #                         cmd = unpackCmdFromJson(jsondict)
                    #                         if cmd:
                    #                             runCmd(cmd)
                    status = 'Done(Success)'
                    if not _isDeleteVM(the_cmd_key):
                        write_result_to_server(group, version, 'default', plural, metadata_name)
                except libvirtError:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except ExecuteException, e:
                    logger.error('Oops! ', exc_info=1)
                    if _isInstallVMFromISO(the_cmd_key) or _isInstallVMFromImage(the_cmd_key):
                        try:
                            if is_vm_exists(metadata_name) and is_vm_active(metadata_name):
                                destroy(metadata_name)
                                time.sleep(0.5)
                        except:
                            logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                finally:
                    if the_cmd_key and operation_type != 'DELETED':
                        time_end = now_to_datetime()
                        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                        involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                        (time_end - time_start).total_seconds())
                        event.set_message(message)
                        event.set_time_end(time_end)
                        try:
                            event.updateKubernetesEvent()
                        except:
                            logger.warning('Oops! ', exc_info=1)
        except ExecuteException, e:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)
        except:
            logger.warning('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)


def vMDiskWatcher(group=GROUP_VM_DISK, version=VERSION_VM_DISK, plural=PLURAL_VM_DISK):
    watcher = watch.Watch()
    kwargs = {}
    kwargs['label_selector'] = LABEL
    kwargs['watch'] = True
    kwargs['timeout_seconds'] = int(TIMEOUT)
    for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                   group=group, version=version, plural=plural, **kwargs):
        try:
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            metadata_name = getMetadataName(jsondict)
        except:
            logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('metadata name: %s' % metadata_name)
            the_cmd_key = _getCmdKey(jsondict)
            logger.debug('cmd key is: %s' % the_cmd_key)
            if the_cmd_key and operation_type != 'DELETED':
                involved_object_name = metadata_name
                involved_object_kind = 'VirtualMachineDisk'
                event_metadata_name = randomUUID()
                event_type = 'Normal'
                status = 'Doing(Success)'
                reporter = 'virtctl'
                event_id = _getEventId(jsondict)
                time_now = now_to_datetime()
                time_start = time_now
                time_end = time_now
                message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                (time_end - time_start).total_seconds())
                event = UserDefinedEvent(event_metadata_name, time_start, time_end, involved_object_name,
                                         involved_object_kind, message, the_cmd_key, event_type)
                try:
                    event.registerKubernetesEvent()
                except:
                    logger.error('Oops! ', exc_info=1)
                pool_name = _get_field(jsondict, the_cmd_key, 'pool')
                disk_type = _get_field(jsondict, the_cmd_key, 'type')
                jsondict = forceUsingMetadataName(metadata_name, the_cmd_key, jsondict)
                cmd = unpackCmdFromJson(jsondict, the_cmd_key)
                if cmd.find('backing-vol-format') >= 0:
                    cmd = cmd.replace('backing-vol-format', 'backing_vol_format')
                if cmd.find('backing-vol') >= 0:
                    cmd = cmd.replace('backing-vol', 'backing_vol')
                #             jsondict = _injectEventIntoLifecycle(jsondict, event.to_dict())
                #             body = jsondict['raw_object']
                #             try:
                #                 client.CustomObjectsApi().replace_namespaced_custom_object(group=group, version=version, namespace='default', plural=plural, name=metadata_name, body=body)
                #             except:
                #                 logger.warning('Oops! ', exc_info=1)
                try:
                    if disk_type is None or pool_name is None:
                        raise ExecuteException('VirtctlError', "disk type and pool must be set")
                    if operation_type == 'ADDED':
                        if cmd:
                            if cmd.find("kubesds-adm") >= 0:
                                logger.debug(cmd)
                                _, data = None, None
                                if not is_kubesds_disk_exists(disk_type, pool_name, metadata_name):
                                    _, data = runCmdWithResult(cmd)
                                else:
                                    _, data = get_kubesds_disk_info(disk_type, pool_name, metadata_name)
                            else:
                                runCmd(cmd)
                                _, data = get_kubesds_disk_info(disk_type, pool_name, metadata_name)
                    elif operation_type == 'MODIFIED':
                        _, data = None, None
                        try:
                            if cmd.find("kubesds-adm") >= 0:
                                result, data = runCmdWithResult(cmd, raise_it=False)
                                if result['code'] != 0:
                                    raise ExecuteException('virtctl', 'error when delete pool ' + result['msg'])
                            else:
                                logger.debug(cmd)
                                runCmd(cmd)
                                _, data = get_kubesds_disk_info(disk_type, pool_name, metadata_name)
                        except Exception, e:
                            if _isDeleteDisk(the_cmd_key) or _isDeleteDiskExternalSnapshot(the_cmd_key) and result[
                                'code'] != 221 and not is_kubesds_disk_exists(disk_type, pool_name, metadata_name):
                                logger.warning("***Disk %s not exists, delete it from virtlet" % metadata_name)
                                # jsondict = deleteLifecycleInJson(jsondict)
                                # try:
                                #     modifyStructure(metadata_name, jsondict, group, version, plural)
                                # except Exception:
                                #     pass
                                # time.sleep(0.5)
                                # if the disk path is alive, do not delete (the reason maybe caused by give the wrong poolname)
                                DISK_PATH = get_disk_path_from_server(metadata_name)
                                if DISK_PATH is None or not os.path.exists(DISK_PATH):
                                    deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                                else:
                                    raise e
                            else:
                                raise e
                        # update disk info
                        if _isCloneDisk(the_cmd_key):
                            if disk_type == 'uus':
                                # uus disk type register to server by hand
                                _, data = get_kubesds_disk_info(disk_type, pool_name, metadata_name)
                                newname = getCloneDiskName(the_cmd_key, jsondict)
                                _, newdata = get_kubesds_disk_info(disk_type, pool_name, newname)
                                addResourceToServer(the_cmd_key, jsondict, newname, newdata, group, version, plural)
                        elif _isDeleteDisk(the_cmd_key) and disk_type == 'uus':
                            deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                    #                     elif operation_type == 'DELETED':
                    #                         if pool_name and is_volume_exists(metadata_name, pool_name):
                    #                             if cmd:
                    #                                 runCmd(cmd)
                    #                         else:
                    #                             raise ExecuteException('VirtctlError', 'No vol %s in pool %s!' % (metadata_name, pool_name))
                    status = 'Done(Success)'
                    if not _isDeleteDisk(the_cmd_key) and not _isDeleteDiskExternalSnapshot(the_cmd_key):
                        write_result_to_server(group, version, 'default', plural, metadata_name, data=data)
                except libvirtError:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except ExecuteException, e:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                finally:
                    if the_cmd_key and operation_type != 'DELETED':
                        time_end = now_to_datetime()
                        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                        involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                        (time_end - time_start).total_seconds())
                        event.set_message(message)
                        event.set_time_end(time_end)
                        try:
                            event.updateKubernetesEvent()
                        except:
                            logger.warning('Oops! ', exc_info=1)
        except ExecuteException, e:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)
        except:
            logger.warning('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)


def vMDiskImageWatcher(group=GROUP_VM_DISK_IMAGE, version=VERSION_VM_DISK_IMAGE, plural=PLURAL_VM_DISK_IMAGE):
    watcher = watch.Watch()
    kwargs = {}
    kwargs['label_selector'] = LABEL
    kwargs['watch'] = True
    kwargs['timeout_seconds'] = int(TIMEOUT)
    for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                   group=group, version=version, plural=plural, **kwargs):
        try:
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            metadata_name = getMetadataName(jsondict)
        except:
            logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('metadata name: %s' % metadata_name)
            the_cmd_key = _getCmdKey(jsondict)
            logger.debug('cmd key is: %s' % the_cmd_key)
            if the_cmd_key and operation_type != 'DELETED':
                involved_object_name = metadata_name
                involved_object_kind = 'VirtualMachineDiskImage'
                event_metadata_name = randomUUID()
                event_type = 'Normal'
                status = 'Doing(Success)'
                reporter = 'virtctl'
                event_id = _getEventId(jsondict)
                time_now = now_to_datetime()
                time_start = time_now
                time_end = time_now
                message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                (time_end - time_start).total_seconds())
                event = UserDefinedEvent(event_metadata_name, time_start, time_end, involved_object_name,
                                         involved_object_kind, message, the_cmd_key, event_type)
                try:
                    event.registerKubernetesEvent()
                except:
                    logger.error('Oops! ', exc_info=1)
                (jsondict, operation_queue, rollback_operation_queue) \
                    = _vmdi_prepare_step(the_cmd_key, jsondict, metadata_name)
                jsondict = forceUsingMetadataName(metadata_name, the_cmd_key, jsondict)
                cmd = unpackCmdFromJson(jsondict, the_cmd_key)
                #             jsondict = _injectEventIntoLifecycle(jsondict, event.to_dict())
                #             body = jsondict['raw_object']
                #             try:
                #                 client.CustomObjectsApi().replace_namespaced_custom_object(group=group, version=version, namespace='default', plural=plural, name=metadata_name, body=body)
                #             except:
                #                 logger.warning('Oops! ', exc_info=1)
                try:
                    if operation_type == 'ADDED':
                        if cmd:
                            runCmd(cmd)
                    elif operation_type == 'MODIFIED':
                        try:
                            runCmd(cmd)
                        except Exception, e:
                            if _isDeleteDiskImage(the_cmd_key):
                                logger.warning("***Disk image %s not exists, delete it from virtlet" % metadata_name)
                                # jsondict = deleteLifecycleInJson(jsondict)
                                # modifyStructure(metadata_name, jsondict, group, version, plural)
                                # time.sleep(0.5)
                                deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                            else:
                                raise e
                        #                     elif operation_type == 'DELETED':
                        #                         if cmd:
                        #                             runCmd(cmd)
                        '''
                        Run operations
                        '''
                        if operation_queue:
                            index = 0
                            for operation in operation_queue:
                                logger.debug(operation)
                                try:
                                    runCmd(operation)
                                except ExecuteException, e:
                                    if index >= len(rollback_operation_queue):
                                        index = len(rollback_operation_queue)
                                    operations_rollback_queue = rollback_operation_queue[:index]
                                    operations_rollback_queue.reverse()
                                    for operation in operations_rollback_queue:
                                        logger.debug("do rollback: %s" % operation)
                                        try:
                                            runCmd(operation)
                                        except:
                                            logger.debug('Oops! ', exc_info=1)
                                    raise e
                                index += 1
                                time.sleep(1)
                    status = 'Done(Success)'
                    if not _isDeleteDiskImage(the_cmd_key):
                        write_result_to_server(group, version, 'default', plural, metadata_name)
                except libvirtError:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except ExecuteException, e:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                finally:
                    if the_cmd_key and operation_type != 'DELETED':
                        time_end = now_to_datetime()
                        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                        involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                        (time_end - time_start).total_seconds())
                        event.set_message(message)
                        event.set_time_end(time_end)
                        try:
                            event.updateKubernetesEvent()
                        except:
                            logger.warning('Oops! ', exc_info=1)
        except ExecuteException, e:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)
        except:
            logger.warning('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)


def vMImageWatcher(group=GROUP_VMI, version=VERSION_VMI, plural=PLURAL_VMI):
    watcher = watch.Watch()
    kwargs = {}
    kwargs['label_selector'] = LABEL
    kwargs['watch'] = True
    kwargs['timeout_seconds'] = int(TIMEOUT)
    for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                   group=group, version=version, plural=plural, **kwargs):
        try:
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            metadata_name = getMetadataName(jsondict)
        except:
            logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('metadata name: %s' % metadata_name)
            the_cmd_key = _getCmdKey(jsondict)
            logger.debug('cmd key is: %s' % the_cmd_key)
            if the_cmd_key and operation_type != 'DELETED':
                if _isCreateImage(the_cmd_key):
                    jsondict = addDefaultSettings(jsondict, the_cmd_key)
                jsondict = forceUsingMetadataName(metadata_name, the_cmd_key, jsondict)
                cmd = unpackCmdFromJson(jsondict, the_cmd_key)
                involved_object_name = metadata_name
                involved_object_kind = 'VirtualMachineImage'
                event_metadata_name = randomUUID()
                event_type = 'Normal'
                status = 'Doing(Success)'
                reporter = 'virtctl'
                event_id = _getEventId(jsondict)
                time_now = now_to_datetime()
                time_start = time_now
                time_end = time_now
                message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                (time_end - time_start).total_seconds())
                event = UserDefinedEvent(event_metadata_name, time_start, time_end, involved_object_name,
                                         involved_object_kind, message, the_cmd_key, event_type)
                try:
                    event.registerKubernetesEvent()
                except:
                    logger.error('Oops! ', exc_info=1)
                #             jsondict = _injectEventIntoLifecycle(jsondict, event.to_dict())
                #             body = jsondict['raw_object']
                #             try:
                #                 client.CustomObjectsApi().replace_namespaced_custom_object(group=group, version=version, namespace='default', plural=plural, name=metadata_name, body=body)
                #             except:
                #                 logger.warning('Oops! ', exc_info=1)
                try:
                    if operation_type == 'ADDED':
                        if _isCreateImage(the_cmd_key):
                            if cmd:
                                runCmd(cmd)
                            if is_vm_exists(metadata_name):
                                if is_vm_active(metadata_name):
                                    destroy(metadata_name)
                                runCmd('/usr/bin/vmm convert_vm_to_image --name %s' % metadata_name)
                        else:
                            if cmd:
                                runCmd(cmd)
                    elif operation_type == 'MODIFIED':
                        try:
                            runCmd(cmd)
                        except Exception, e:
                            if _isDeleteImage(the_cmd_key):
                                logger.warning("***VM image %s not exists, delete it from virtlet" % metadata_name)
                                # jsondict = deleteLifecycleInJson(jsondict)
                                # modifyStructure(metadata_name, jsondict, group, version, plural)
                                # time.sleep(0.5)
                                deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                            else:
                                raise e
                    #                     elif operation_type == 'DELETED':
                    #                         if is_vm_active(metadata_name):
                    #                             destroy(metadata_name)
                    #                         if cmd:
                    #                             runCmd(cmd)
                    status = 'Done(Success)'
                    if not _isDeleteVMImage(the_cmd_key):
                        write_result_to_server(group, version, 'default', plural, metadata_name)
                except libvirtError:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except ExecuteException, e:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                finally:
                    if the_cmd_key and operation_type != 'DELETED':
                        time_end = now_to_datetime()
                        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                        involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                        (time_end - time_start).total_seconds())
                        event.set_message(message)
                        event.set_time_end(time_end)
                        try:
                            event.updateKubernetesEvent()
                        except:
                            logger.warning('Oops! ', exc_info=1)
        except ExecuteException, e:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)
        except:
            logger.warning('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)


def vMSnapshotWatcher(group=GROUP_VM_SNAPSHOT, version=VERSION_VM_SNAPSHOT, plural=PLURAL_VM_SNAPSHOT):
    watcher = watch.Watch()
    kwargs = {}
    kwargs['label_selector'] = LABEL
    kwargs['watch'] = True
    kwargs['timeout_seconds'] = int(TIMEOUT)
    for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                   group=group, version=version, plural=plural, **kwargs):
        try:
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            metadata_name = getMetadataName(jsondict)
        except:
            logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('metadata name: %s' % metadata_name)
            the_cmd_key = _getCmdKey(jsondict)
            logger.debug('cmd key is: %s' % the_cmd_key)
            if the_cmd_key and operation_type != 'DELETED':
                involved_object_name = metadata_name
                involved_object_kind = 'VirtualMachineSnapshot'
                event_metadata_name = randomUUID()
                event_type = 'Normal'
                status = 'Doing(Success)'
                reporter = 'virtctl'
                event_id = _getEventId(jsondict)
                time_now = now_to_datetime()
                time_start = time_now
                time_end = time_now
                message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                (time_end - time_start).total_seconds())
                event = UserDefinedEvent(event_metadata_name, time_start, time_end, involved_object_name,
                                         involved_object_kind, message, the_cmd_key, event_type)
                try:
                    event.registerKubernetesEvent()
                except:
                    logger.error('Oops! ', exc_info=1)
                vm_name = _get_field(jsondict, the_cmd_key, 'domain')
                if not vm_name:
                    raise ExecuteException('VirtctlError', 'error: no "domain" parameter')
                if not is_vm_exists(vm_name):
                    raise ExecuteException('VirtctlError', '404, Not Found. VM %s not exists.' % vm_name)
                (jsondict, snapshot_operations_queue, snapshot_operations_rollback_queue) = _vm_snapshot_prepare_step(
                    the_cmd_key, jsondict, metadata_name)
                jsondict = forceUsingMetadataName(metadata_name, the_cmd_key, jsondict)
                cmd = unpackCmdFromJson(jsondict, the_cmd_key)
                #             jsondict = _injectEventIntoLifecycle(jsondict, event.to_dict())
                #             body = jsondict['raw_object']
                #             try:
                #                 client.CustomObjectsApi().replace_namespaced_custom_object(group=group, version=version, namespace='default', plural=plural, name=metadata_name, body=body)
                #             except:
                #                 logger.warning('Oops! ', exc_info=1)
                try:
                    if operation_type == 'ADDED':
                        if cmd:
                            runCmd(cmd)
                    elif operation_type == 'MODIFIED':
                        try:
                            runCmd(cmd)
                        except Exception, e:
                            if _isDeleteVMSnapshot(the_cmd_key) and not _snapshot_file_exists(metadata_name):
                                logger.warning("***VM snapshot %s not exists, delete it from virtlet" % metadata_name)
                                # jsondict = deleteLifecycleInJson(jsondict)
                                # modifyStructure(metadata_name, jsondict, group, version, plural)
                                # time.sleep(0.5)
                                deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                            else:
                                raise e
                        '''
                        Run snapshot operations
                        '''
                        if snapshot_operations_queue:
                            index = 0
                            for operation in snapshot_operations_queue:
                                logger.debug(operation)
                                try:
                                    runCmd(operation)
                                except ExecuteException, e:
                                    if index >= len(snapshot_operations_rollback_queue):
                                        index = len(snapshot_operations_rollback_queue)
                                    snapshot_operations_rollback_queue = snapshot_operations_rollback_queue[:index]
                                    snapshot_operations_rollback_queue.reverse()
                                    for operation in snapshot_operations_rollback_queue:
                                        logger.debug("do rollback: %s" % operation)
                                        try:
                                            runCmd(operation)
                                        except:
                                            logger.debug('Oops! ', exc_info=1)
                                    raise e
                                index += 1
                                time.sleep(1)
                    #                     elif operation_type == 'DELETED':
                    # #                         if vm_name and is_snapshot_exists(metadata_name, vm_name):
                    #                         if cmd:
                    #                             runCmd(cmd)
                    status = 'Done(Success)'
                    if not _isDeleteVMSnapshot(the_cmd_key):
                        write_result_to_server(group, version, 'default', plural, metadata_name)
                except libvirtError:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except ExecuteException, e:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                finally:
                    if the_cmd_key and operation_type != 'DELETED':
                        time_end = now_to_datetime()
                        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                        involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                        (time_end - time_start).total_seconds())
                        event.set_message(message)
                        event.set_time_end(time_end)
                        try:
                            event.updateKubernetesEvent()
                        except:
                            logger.warning('Oops! ', exc_info=1)
        except ExecuteException, e:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)
        except:
            logger.warning('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)


def vMNetworkWatcher(group=GROUP_VM_NETWORK, version=VERSION_VM_NETWORK, plural=PLURAL_VM_NETWORK):
    watcher = watch.Watch()
    kwargs = {}
    kwargs['label_selector'] = LABEL
    kwargs['watch'] = True
    kwargs['timeout_seconds'] = int(TIMEOUT)
    for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                   group=group, version=version, plural=plural, **kwargs):
        try:
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            metadata_name = getMetadataName(jsondict)
        except:
            logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('metadata name: %s' % metadata_name)
            the_cmd_key = _getCmdKey(jsondict)
            logger.debug('cmd key is: %s' % the_cmd_key)
            if the_cmd_key and operation_type != 'DELETED':
                involved_object_name = metadata_name
                involved_object_kind = 'VirtualMachineNetwork'
                event_metadata_name = randomUUID()
                event_type = 'Normal'
                status = 'Doing(Success)'
                reporter = 'virtctl'
                event_id = _getEventId(jsondict)
                time_now = now_to_datetime()
                time_start = time_now
                time_end = time_now
                message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                (time_end - time_start).total_seconds())
                event = UserDefinedEvent(event_metadata_name, time_start, time_end, involved_object_name,
                                         involved_object_kind, message, the_cmd_key, event_type)
                try:
                    event.registerKubernetesEvent()
                except:
                    logger.error('Oops! ', exc_info=1)
                if not _isDeleteSwPort(the_cmd_key):
                    jsondict = forceUsingMetadataName(metadata_name, the_cmd_key, jsondict)
                cmd = unpackCmdFromJson(jsondict, the_cmd_key)
                #             jsondict = _injectEventIntoLifecycle(jsondict, event.to_dict())
                #             body = jsondict['raw_object']
                #             try:
                #                 client.CustomObjectsApi().replace_namespaced_custom_object(group=group, version=version, namespace='default', plural=plural, name=metadata_name, body=body)
                #             except:
                #                 logger.warning('Oops! ', exc_info=1)
                try:
                    if operation_type == 'ADDED':
                        if cmd:
                            runCmd(cmd)
                    elif operation_type == 'MODIFIED':
                        try:
                            runCmd(cmd)
                            if _isDeleteNetwork(the_cmd_key) or _isDeleteBridge(the_cmd_key):
                                deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                        except Exception, e:
                            if _isDeleteNetwork(the_cmd_key) or _isDeleteBridge(the_cmd_key):
                                logger.warning("***Network %s not exists, delete it from virtlet" % metadata_name)
                                # jsondict = deleteLifecycleInJson(jsondict)
                                # modifyStructure(metadata_name, jsondict, group, version, plural)
                                # time.sleep(0.5)
                                deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                            else:
                                raise e
                    elif operation_type == 'DELETED':
                        if cmd:
                            runCmd(cmd)
                    status = 'Done(Success)'
                    if not _isDeleteNetwork(the_cmd_key) and not _isDeleteBridge(the_cmd_key):
                        write_result_to_server(group, version, 'default', plural, metadata_name,
                                               the_cmd_key=the_cmd_key)
                except libvirtError:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except ExecuteException, e:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                finally:
                    if the_cmd_key and operation_type != 'DELETED':
                        time_end = now_to_datetime()
                        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                        involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                        (time_end - time_start).total_seconds())
                        event.set_message(message)
                        event.set_time_end(time_end)
                        try:
                            event.updateKubernetesEvent()
                        except:
                            logger.warning('Oops! ', exc_info=1)
        except ExecuteException, e:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)
        except:
            logger.warning('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)


def vMPoolWatcher(group=GROUP_VM_POOL, version=VERSION_VM_POOL, plural=PLURAL_VM_POOL):
    watcher = watch.Watch()
    kwargs = {}
    kwargs['label_selector'] = LABEL
    kwargs['watch'] = True
    kwargs['timeout_seconds'] = int(TIMEOUT)
    for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                   group=group, version=version, plural=plural, **kwargs):
        try:
            operation_type = jsondict.get('type')
            logger.debug(operation_type)
            metadata_name = getMetadataName(jsondict)
        except:
            logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('metadata name: %s' % metadata_name)
            the_cmd_key = _getCmdKey(jsondict)
            logger.debug('cmd key is: %s' % the_cmd_key)
            if the_cmd_key and operation_type != 'DELETED':
                involved_object_name = metadata_name
                involved_object_kind = 'VirtualMachinePool'
                event_metadata_name = randomUUID()
                event_type = 'Normal'
                status = 'Doing(Success)'
                reporter = 'virtctl'
                event_id = _getEventId(jsondict)
                time_now = now_to_datetime()
                time_start = time_now
                time_end = time_now
                message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                (time_end - time_start).total_seconds())
                event = UserDefinedEvent(event_metadata_name, time_start, time_end, involved_object_name,
                                         involved_object_kind, message, the_cmd_key, event_type)
                try:
                    event.registerKubernetesEvent()
                except:
                    logger.error('Oops! ', exc_info=1)
                pool_name = metadata_name
                pool_type = getPoolType(the_cmd_key, jsondict)
                logger.debug("pool_name is :" + pool_name)
                logger.debug("pool_type is :" + pool_type)
                jsondict = forceUsingMetadataName(metadata_name, the_cmd_key, jsondict)
                cmd = unpackCmdFromJson(jsondict, the_cmd_key)
                try:
                    if operation_type == 'ADDED':
                        # judge pool path exist or not

                        # POOL_PATH = getPoolPathWhenCreate(jsondict)
                        # # file_dir = os.path.split(POOL_PATH)[0]
                        # if not os.path.isdir(POOL_PATH):
                        #     os.makedirs(POOL_PATH)
                        if not is_kubesds_pool_exists(pool_type, pool_name):
                            _, poolJson = runCmdWithResult(cmd)
                            logger.debug('create pool')
                        else:
                            _, poolJson = get_kubesds_pool_info(pool_type, pool_name)
                            logger.debug('get pool info')
                    elif operation_type == 'MODIFIED':
                        try:
                            if _isDeletePool(the_cmd_key):
                                result, _ = runCmdWithResult(cmd, raise_it=False)
                                # fix pool type not match
                                if result['code'] == 0:
                                    deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                                else:
                                    raise ExecuteException('virtctl', 'error when delete pool ' + result['msg'])
                            else:
                                if pool_type == 'uus':
                                    pass
                                else:
                                    runCmd(cmd)
                        except Exception, e:
                            # only two case has exception when delete pool
                            # case 1: pool exist but not pool type not match(code is 221)
                            # case 2: pool not exist, only this case delete pool info from api server
                            if _isDeletePool(the_cmd_key) and result['code'] != 221 and not is_kubesds_pool_exists(
                                    pool_type, pool_name):
                                logger.warning("***Pool %s not exists, delete it from virtlet" % metadata_name)
                                # jsondict = deleteLifecycleInJson(jsondict)
                                # modifyStructure(metadata_name, jsondict, group, version, plural)
                                # time.sleep(0.5)
                                deleteStructure(metadata_name, V1DeleteOptions(), group, version, plural)
                            else:
                                raise e
                        if not _isDeletePool(the_cmd_key):
                            result, poolJson = get_kubesds_pool_info(pool_type, pool_name)
                    # elif operation_type == 'DELETED':
                    #     if is_pool_exists(pool_name):
                    #         runCmd(cmd)
                    #     else:
                    #         raise ExecuteException('VirtctlError', 'Not exist '+pool_name+' pool!')
                    status = 'Done(Success)'
                    if not _isDeletePool(the_cmd_key):
                        write_result_to_server(group, version, 'default', plural,
                                               metadata_name, {'code': 0, 'msg': 'success'}, poolJson)
                except libvirtError:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except ExecuteException, e:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                except:
                    logger.error('Oops! ', exc_info=1)
                    info = sys.exc_info()
                    try:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
                    except:
                        logger.warning('Oops! ', exc_info=1)
                    status = 'Done(Error)'
                    event_type = 'Warning'
                    event.set_event_type(event_type)
                finally:
                    if the_cmd_key and operation_type != 'DELETED':
                        time_end = now_to_datetime()
                        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' % (
                        involved_object_kind, involved_object_name, the_cmd_key, status, reporter, event_id,
                        (time_end - time_start).total_seconds())
                        event.set_message(message)
                        event.set_time_end(time_end)
                        try:
                            event.updateKubernetesEvent()
                        except:
                            logger.warning('Oops! ', exc_info=1)
        except ExecuteException, e:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, e.reason, e.message, group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)
        except:
            logger.warning('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), group, version, plural)
            except:
                logger.warning('Oops! ', exc_info=1)


