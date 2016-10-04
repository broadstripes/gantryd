def getContainerIPAddress(client, container):
  """ Returns the IP address on which the container is running. """
  container_info = client.inspect_container(container)
  return container_info['NetworkSettings']['IPAddress']

def getContainerExternalPort(client, container):
  """ Returns the external port used for the ELB """
  container_info = client.inspect_container(container)
  return int(container_info['NetworkSettings']['Ports']["80/tcp"][0]['HostPort'])
