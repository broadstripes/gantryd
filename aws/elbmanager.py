from elb import ELB
from runtime.metadata import setContainerStatus
from health.checks import buildHealthCheck
from util import report, ReportLevels
import time

class ELBManager(object):
  def __init__(self, target_group_arn):
    self.elb = ELB(target_group_arn)
    self.ports = {}
  
  def adjustForUpdatingComponent(self, component, started_container):
    # Add container to target group in ELB
    self.registerContainer()

    # Now wait until all of the elb checks/conditions are met
    checks = []
    for check in component.config.elb_checks:
      checks.append((check, buildHealthCheck(check)))

    report('Waiting for %s elb checks' % len(checks), component=component)

    for (config, check) in checks:
      check_passed = False

      while not check_passed:
        report('Running elb check: ' + config.getTitle(), component=component)
        result = check.run(started_container, report)
        if not result:
          report('Elb check failed', component=component)

          report('Sleeping ' + str(config.timeout) + ' second(s)...', component=component)
          time.sleep(config.timeout)
        else:
          check_passed = True

    report('Elb check finished', level=ReportLevels.BACKGROUND)

    setContainerStatus(started_container, 'running')

  def registerContainer(self):
    self.elb.registerContainer(self.newPort())
  
  def deregisterContainer(self):
    self.elb.deregisterContainer(self.oldPort())

  def deregisterAllContainers(self):
    self.elb.deregisterContainer(80)
    self.elb.deregisterContainer(81)

  def determinePortNumber(self):
    """ Alternate between ports 80 and 81 based off of the currently regiesterd port for this instance """
    if self.elb.describeContainerHealth(80) == 'unused':
      self.ports['new'] = 80
      self.ports['old'] = 81
    elif self.elb.describeContainerHealth(81) == 'unused':
      self.ports['new'] = 81
      self.ports['old'] = 80
    elif self.elb.describeContainerHealth(80) == 'unhealthy':
      self.ports['new'] = 80
      self.ports['old'] = 81
    else:
      self.ports['new'] = 81
      self.ports['old'] = 80
  
  def oldPort(self):
    return self.ports['old']

  def newPort(self):
    return self.ports['new']
