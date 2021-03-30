from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.packet.arp import arp
from pox.lib.util import dpidToStr
from pox.lib.addresses import IPAddr, EthAddr
from random import randint

log = core.getLogger()

IDLE_TIMEOUT = 100
HARD_TIMEOUT = 300

IP_TYPE = 0x800
ARP_TYPE = 0x806

"""
Main idea of algorithm:
1) When a switch come up, we know previously which hosts are in which port and we install
rules for 'in-switch' traffic.
2) For connections of hosts in different switches, transform into switch connections
3) Find all possible paths between the given switches
3.a) select randomly one of the paths
4) Install rules in the switches so that the hosts can communicate
"""
class RandomPaths (object):

  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Adjacency list of switches
    self.switches = {
                      9: set([10,11]),
                     10: set([9,13]),
                     11: set([9,12,13]),
                     12: set([11]),
                     13: set([10,11])
                    }

    # List of ports connecting other switches for each switch
    self.switches_ports = {
                            9: {10: 4, 11: 5},
                           10: {9: 2, 13: 3},
                           11: {9: 2, 12: 3, 13: 4},
                           12: {11: 2},
                           13: {10: 3, 11: 4}}

    self.ip_to_switch_port = dict({
                                   '10.0.0.1': [9,1],
                                   '10.0.0.2': [9,2],
                                   '10.0.0.3': [9,3],
                                   '10.0.0.4': [10,1],
                                   '10.0.0.5': [11,1],
                                   '10.0.0.6': [12,1],
                                   '10.0.0.7': [13,1],
                                   '10.0.0.8': [13,2]
                                  })

    # Switch DPID [ip1..ipn]
    self.switch_ips = dict({
                             9:['10.0.0.1','10.0.0.2', '10.0.0.3'],
                            10:['10.0.0.4'],
                            11:['10.0.0.5'],
                            12:['10.0.0.6'],
                            13:['10.0.0.7','10.0.0.8']})

  #OK
  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)

  # Use: list(dfs_paths(graph, 'A', 'F'))
  def dfs_paths(self, graph, start, goal):
    stack = [(start, [start])]
    while stack:
      (vertex, path) = stack.pop()
      for next in graph[vertex] - set(path):
        if next == goal:
          yield path + [next]
        else:
          stack.append((next, path + [next]))

  #ok
  # This installs a path for the flow between two different switches
  def install_flow_path(self, path, src_ip, dst_ip):
    # Path length always >= 2
    prev = path[0] # First hop 
    for switch in path[1:(len(path))]: # Dont need to install rule to the last switch in the path
      log.debug("Flow from switch %s to switch %s", prev, switch)
      msg = of.ofp_flow_mod()
      msg.idle_timeout = IDLE_TIMEOUT
      msg.hard_timeout = HARD_TIMEOUT
      msg.match.dl_type = IP_TYPE
      msg.match.nw_src = IPAddr(src_ip)
      msg.match.nw_dst = IPAddr(dst_ip)
      #msg.data = event.ofp
      output_port = self.switches_ports[prev][switch]
      msg.actions.append(of.ofp_action_output(port = output_port))
      core.openflow.getConnection(prev).send(msg)
      msg.match.dl_type = ARP_TYPE
      core.openflow.getConnection(prev).send(msg)
      log.debug("At switch %s rule for %s -> %s installed", prev, src_ip, dst_ip)
      log.debug("At switch %s output port %s to switch %s", prev, output_port, switch)
      prev = switch

  # I nstall basic rules when switches come up
  def _handle_ConnectionUp (self, event):
    dpid = self.connection.dpid
    ips = self.switch_ips[self.connection.dpid]
    
    for dstip in ips:
      msg = of.ofp_flow_mod()
      msg.idle_timeout = of.OFP_FLOW_PERMANENT
      msg.hard_timeout = of.OFP_FLOW_PERMANENT
      msg.match.dl_type = IP_TYPE
      msg.match.nw_dst = IPAddr(dstip)
      msg.actions.append(of.ofp_action_output(port = self.ip_to_switch_port[dstip][1]))
      #self.connection.send(msg)
      core.openflow.getConnection(dpid).send(msg)
      msg.match.dl_type = ARP_TYPE
      #self.connection.send(msg)
      core.openflow.getConnection(dpid).send(msg)
      log.debug("At switch %s rule for dst %s installed", dpid, dstip)

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    log.debug("New packet from switch %s", self.connection.dpid)
    packet = event.parsed # This is the parsed packet data.

    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    if packet.type == packet.ARP_TYPE:
      src_ip = str(packet.payload.protosrc)
      dst_ip = str(packet.payload.protodst)
      log.debug("New ARP packet %s -> %s", src_ip, dst_ip)
    elif packet.type == packet.IP_TYPE:
      src_ip = str(packet.next.srcip)
      dst_ip = str(packet.next.dstip)
      log.debug("New IP packet %s -> %s", src_ip, dst_ip)
    else:
      log.debug("Ignoring packet type %s", packet.type)
      return      

    src_switch = self.ip_to_switch_port[src_ip][0]
    dst_switch = self.ip_to_switch_port[dst_ip][0]

    log.debug("Generating paths from switch %s to %s", src_switch, dst_switch)

    paths = list(self.dfs_paths(self.switches, src_switch, dst_switch))    
    log.debug("Possible paths: %s", paths)
    if ((len(paths) - 1) < 0):
      log.debug("No path between switches %s -> %s found", src_switch, dst_switch)
      return
    else:
      rand = randint(0, len(paths) - 1)
    path = paths[rand]

    log.debug("Choosen path %s", path)
    reverse_path = path[::-1]

    # Install flow rules in the switches for both directions of the connection
    log.debug("Installing rule for the reverse path %s", reverse_path)
    self.install_flow_path(reverse_path, dst_ip, src_ip)

    log.debug("Installing rule for path %s", path)    
    self.install_flow_path(path, src_ip, dst_ip)
    
    # Message back to switch so it can forward the packet
    msg = of.ofp_packet_out()
    msg.data = packet
    # Send message to switch
    self.connection.send(msg)

def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling switch %s" % (event.connection,))
    RandomPaths(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
  