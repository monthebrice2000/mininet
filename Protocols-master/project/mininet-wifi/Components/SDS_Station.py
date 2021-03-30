#!/usr/bin/pyhton

from mininet.wifi.node import Station
from .config import Modes, Type


class SDStorage_Station(Station):
    "Storage Station is a host that operates with a wireless interface card"

    def __init__(self, name, custom_type=Type.SD_STATION, NO_of_Dir=0, NO_of_files=0, file_size=0, Used_space=0, **pars):
        Station.__init__(self, name, **pars)
        self.NO_of_files = NO_of_files
        self.NO_of_Dir = NO_of_Dir
        self.file_size = file_size
        self.Used_space = Used_space
        self.custom_type = custom_type

    # print ("Custom station has been initialized")

    def requestContents(self, content_identifier, mode, net):
        if (mode == Modes.MEC):
            """MEC SEARCH"""
            """getting accessPoint the station is associated to"""
            ap = self.params['associatedTo'][0]

            # request AR content from associated accessPoint first
            index = 0
            for accessPoint in net.aps:
                if (accessPoint.params['mac'] == ap.params['mac']):
                    result = net.aps[index].handleContentRequest(
                        content_identifier, net)
                    # print ("result in station: %s"%result)
                    break
                else:
                    index += 1

            # print ("AP[%s] returned %s for the requested AR content"%(index,result))
            return result

        else:
            """SD Search"""
