import boto3
import urllib2

class ELB(object):
  def __init__(self, target_group_arn):
    self.client = boto3.client('elbv2', region_name='us-east-1')
    self.instance_id = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read()
    self.target_group_arn = target_group_arn

  def registerContainer(self, port):
    response = self.client.register_targets(
      TargetGroupArn=self.target_group_arn,
      Targets=[
          {
            'Id': self.instance_id,
            'Port': port
          },
      ]
    )

  def deregisterContainer(self, port):
    response = self.client.deregister_targets(
      TargetGroupArn=self.target_group_arn,
      Targets=[
          {
            'Id': self.instance_id,
            'Port': port
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
   
  def isTargetHealthy(self, target_port):
    return self.describeContainerHealth(target_port) == 'healthy'

  def isTargetUnused(self, target_port):
    return self.describeContainerHealth(target_port) == 'unused'
