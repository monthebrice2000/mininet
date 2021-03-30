print("Hello World ")

switches = {}
switches_ports = {}

sswitches = {
    9: set([10, 11]),
    10: set([9, 13]),
    11: set([9, 12, 13]),
    12: set([11]),
    13: set([10, 11])
}

sswitches_ports = {
    9: {10: 4, 11: 5},
    10: {9: 2, 13: 3},
    11: {9: 2, 12: 3, 13: 4},
    12: {11: 2},
    13: {10: 3, 11: 4}}


def add_in_switches(dpid1, port1, dpid2, port2):
    if "s" + dpid1 in switches:
        # if( not isinstance( switches[dpid1] , set ) ):
        # switches[ "s"+dpid1 ] = set ( [] )
        switches["s" + dpid1].add("s" + dpid2)
    else:
        switches["s" + dpid1] = set(["s" + dpid2])


def add_in_switches_ports(dpid1, port1, dpid2, port2):
    if 's' + dpid1 in switches_ports:
        switches_ports['s' + dpid1]['s' + dpid2] = port1
    else:
        switches_ports['s' + dpid1] = {}
        switches_ports['s' + dpid1]['s' + dpid2] = port1

energy_capacity = {}
def add_energy_capacity(energy, capacity, ap):
    if ap in energy_capacity:
        energy_capacity[ap]["energy"] = energy
        energy_capacity[ap]["capacity"] = capacity
    else:
        energy_capacity[ap] = {}
        energy_capacity[ap]["energy"] = energy
        energy_capacity[ap]["capacity"] = capacity


def dfs_paths(graph, start, goal):
    stack = [(start, [start])]
    while stack:
        (vertex, path) = stack.pop()
        for next in graph[vertex] - set(path):
            if next == goal:
                yield path + [next]
            else:
                stack.append((next, path + [next]))

def get_min_path( paths ):
    path = []
    if( len(paths) == 0 ):
        return path
    path = paths[0]
    for path_in in paths:
        if len(path) > len( path_in ):
            path = path_in
    return path

def paths_port(list_path):
    stack = []
    prec = 0;
    for elt in list_path:
        if list_path[0] == elt:
            prec = elt
            continue
        stack.append(str(prec) + ' ' + str(sswitches_ports[prec][elt]))
        # print(elt_update)
        prec = elt
    stack.append(str(prec))
    # print( elt_update )
    return stack


if __name__ == '__main__':
    # add_in_switches_ports('9', 4, '10', 2)
    # add_in_switches_ports('9', 5, '11', 2)
    # add_in_switches_ports('9', 5, '11', 2)
    # add_in_switches_ports('12', 2, '11', 2)
    # add_in_switches_ports('13', 3, '11', 4)
    # print( switches_ports )
    # for key in list ( sswitches.keys() ):
    #     for value in list( sswitches[ key ] ) :
    #         add_in_switches( str(key), 4, str( value ), 2 )
    # print( switches_ports )
    # print( list(dfs_paths(sswitches, 10, 12)) )
    # list_3 = get_min_path(  list(dfs_paths(sswitches, 10, 12)) )
    # print(list_3)
    # print ( paths_port( list_3) )

    # print ( list( sswitches.keys() ) )
    # print( list ( sswitches.values() ) )

    # print ( int("s11"[1:] ) )

    add_energy_capacity(str(81.5511349626),str(125000),"ap4");
    add_energy_capacity(str(81.5511349626), str(125000), "ap5");
    add_energy_capacity(str(81.5511349626), str(125000), "ap6");
    add_energy_capacity(str(81.5511349626), str(125000), "ap7");
    add_energy_capacity(str(81.5511349626), str(125000), "ap8");
    add_energy_capacity(str(81.5511349626), str(105000), "ap4");
    print( energy_capacity );