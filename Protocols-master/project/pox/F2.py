# Copyright 2011-2013 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file is loosely based on the discovery component in NOX.

"""
This module discovers the connectivity between OpenFlow switches by sending
out LLDP packets. To be notified of this information, listen to LinkEvents
on core.openflow_discovery.

It's possible that some of this should be abstracted out into a generic
Discovery module, or a Discovery superclass.
"""

from pox.lib.revent import *
from pox.core import core
import socket
import _thread
import time
#from thread import *

log = core.getLogger()
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 1037

energy_capacity = {}

def add_energy_capacity(energy, capacity, ap):
    if ap in energy_capacity:
        energy_capacity[ap]["energy"] = energy
        energy_capacity[ap]["capacity"] = capacity
    else:
        energy_capacity[ap] = {}
        energy_capacity[ap]["energy"] = energy
        energy_capacity[ap]["capacity"] = capacity

class F2(object):

  _core_name = "F2"

  def __init__(self, host, port):
    
    self.host = host
    self.port = port
    self.serverSideSocket = socket.socket()
    self.ThreadCount = 0
    try:
      self.serverSideSocket.bind((self.host, self.port))
    except socket.error as e:
      log.error(str(e))

    log.debug('Socket is listening..')
    self.serverSideSocket.listen(5)
    self.loop()


  def multi_threaded_client(self, connection):
    while True:
        connection.send(str.encode('Hello !'))
        time.sleep(10)
        data = connection.recv(2048)
        if not data:
          break
        else:
          data_rcv = data.decode('utf-8')
          data_split = str(data_rcv).split(',');
          add_energy_capacity( str(data_split[0]), str(data_split[1]), str(data_split[2]))
          log.info( 'data_split'+ str(data_split) );
          log.debug('Received ' + data_rcv)
          print("Received {}".format(data_rcv))
    connection.close()


  def loop(self):
    while True:
      Client, address = self.serverSideSocket.accept()
      log.debug('Connected to: ' + str(address[0]) + ':' + str(address[1]))
      _thread.start_new_thread(self.multi_threaded_client, (Client, ))
      self.ThreadCount += 1
      log.debug('Thread Number: ' + str(self.ThreadCount))
    self.serverSideSocket.close()
  
 
def launch(port = DEFAULT_PORT, host = DEFAULT_HOST ):
  log.info("Launching function pox");
  core.registerNew(F2, host, port)
