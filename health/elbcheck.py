import socket
import urllib2

from health.healthcheck import HealthCheck
from util import ReportLevels
from aws.elb import ELB

class ELBCheck(HealthCheck):
  """ A health check for healthy status on the ELB. """
  def __init__(self, config):
    super(ELBCheck, self).__init__()
    self.config = config
    self.elb_manager = ELB(self.config.elb_target_group_arn)
  
  def run(self, container, report):
    container_port = self.getContainerExternalPort(container)
    report('Checking ELB for healthy status for container ' + container['Id'][0:12] + ': ' + str(container_port),
      level = ReportLevels.EXTRA)

    return self.elb_manager.isTargetHealthy(container_port)

class ELBTerminateCheck(HealthCheck):
  """ A health check for unused status on the ELB. """
  def __init__(self, config):
    super(ELBTerminateCheck, self).__init__()
    self.config = config
    self.elb_manager = ELB(self.config.elb_target_group_arn)
  
  def run(self, container, report):
    container_port = self.getContainerExternalPort(container)
    report('Checking ELB for unused status for container ' + container['Id'][0:12] + ': ' + str(container_port),
      level = ReportLevels.EXTRA)
    return self.elb_manager.isTargetUnused(container_port)