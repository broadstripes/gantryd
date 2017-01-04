import boto3
import urllib2
from runtime.metadata import setContainerStatus

class ELB(object):
  def __init__(self, target_group_arn):
    self.client = boto3.client('elbv2', region_name='us-east-1')
    self.instance_id = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read()
    self.target_group_arn = target_group_arn
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
        result = check.run(container, report)
        if not result:
          report('Elb check failed', component=component)

          report('Sleeping ' + str(config.timeout) + ' second(s)...', component=component)
          time.sleep(config.timeout)
        else:
          check_passed = True

    report('Elb check finished', level=ReportLevels.BACKGROUND)

    setContainerStatus(started_container, 'running')

  def registerContainer(self):
    response = self.client.register_targets(
      TargetGroupArn=self.target_group_arn,
      Targets=[
          {
            'Id': self.instance_id,
            'Port': self.newPort()
          },
      ]
    )
  
  def deregisterContainer(self):
    response = self.client.deregister_targets(
      TargetGroupArn=self.target_group_arn,
      Targets=[
          {
            'Id': self.instance_id,
            'Port': self.oldPort()
          },
      ]
    )

  def deregisterAllContainers(self):
    response = self.client.deregister_targets(
      TargetGroupArn=self.target_group_arn,
      Targets=[
          {
            'Id': self.instance_id,
            'Port': 80
          },
          {
            'Id': self.instance_id,
            'Port': 81
          },
      ]
    )

  def describeContainerHealth(self, target_port):
    response = self.client.describe_target_health(
      TargetGroupArn=self.target_group_arn,
      Targets=[
          {
            'Id': self.instance_id,
            'Port': target_port
          },
      ]
    )

    return response['TargetHealthDescriptions'][0]['TargetHealth']['State']
   
  def determinePortNumber(self):
    """ Alternate between ports 80 and 81 based off of the currently regiesterd port for this instance """
    if self.describeContainerHealth(80) == 'unused':
      self.ports['new'] = 80
      self.ports['old'] = 81
    elif self.describeContainerHealth(81) == 'unused':
      self.ports['new'] = 81
      self.ports['old'] = 80
    elif self.describeContainerHealth(80) == 'unhealthy':
      self.ports['new'] = 80
      self.ports['old'] = 81
    else:
      self.ports['new'] = 81
      self.ports['old'] = 80
  def oldPort(self):
    return self.ports['old']

  def newPort(self):
    return self.ports['new']

  def isTargetHealthy(self, target_port):
    return self.describeContainerHealth(target_port) == 'healthy'

  def isTargetUnused(self, target_port):
    return self.describeContainerHealth(target_port) == 'unused'
