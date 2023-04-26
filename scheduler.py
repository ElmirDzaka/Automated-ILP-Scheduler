"""
Authors:
Elmir Dzaka
Kidus Yohannes

Summary:
This file takes in an edgelist graph and and automatically generates the schedule using ILP solver GLPK,
and produces the Quality-of-Results. Supports ML-RC, MR-LC, or both using Pareto-optimal analysis.

Start date: 4/3/2023
Last updated: 4/25/2023
"""
import sys
import argparse
import networkx as nx


def main(argv):
    parser = argparse.ArgumentParser(
                    prog='Automated ILP Scheduler',
                    description='Automatically generates the schedule and produces the QoRs of the schedule for the given DFG graph. Interfaces with LPKSolver.',
                    epilog='Developed by Elmir and Kidus :cool emoji:')

    parser.add_argument('-l', '--latency', type=int, help="The desired latency to minimize memory under.")
    parser.add_argument('-a', '--area_cost', type=int, help="The desired area cost to minimize latency under.")
    parser.add_argument('-g', '--graph', type=argparse.FileType('r'), help="The desired DFG to automate the schedule for using ILP. It should be in edgelist format.")
    args = parser.parse_args()

    # ensure user inserts a graph
    if args.graph is None:
        print("please insert an edgelist graph using -g")
        exit()

    graph = nx.read_edgelist(args.graph, create_using=nx.DiGraph) # assumes first and last node are source and sink

    # generate cases for which scheduling algorithm to use (MR-LC or ML-RC)
    if args.latency is None and args.area_cost is None:
        print("please insert a latency or area cost restaint using arguments -l or -a ")
        exit()
    elif not args.latency and args.area_cost:
        schedule_obj = "ML-RC"
    elif args.latency and not args.area_cost:
        schedule_obj = "MR-LC"
    elif args.latency and args.area_cost:
        schedule_obj = "both"
    
    print(f"schedule: {schedule_obj}")
    ilp_filename = f"auto_{schedule_obj}.ilp" 
    
    # parse graph and get node units and costs
    node_unit, unit_cost = get_node_unit_cost(graph)
    print("node units:", node_unit)
    print(f"unit_costs: {unit_cost}")

    # TODO error check: make sure there is not a cycle

    # get the unit times for ASAP and ALAP
    unit_times_asap = get_asap(graph)

    t = list(graph.nodes())[-1] # sink node (assumes is the last node)
    asap_latency_cstr = unit_times_asap[t] - 1 # the level before sink is the time of the last unit exec
    latency_cstr = args.latency if args.latency else asap_latency_cstr # either from user supplied latency constraint or ASAP
    if latency_cstr < asap_latency_cstr: # error check: make sure latency isn't too small
        raise Exception(f'Solution not posible, given latency constraint is too small. Should be at least {asap_latency_cstr}.')
    unit_times_alap = get_alap(graph, latency_cstr)
    print("asap: ", unit_times_asap, "\nalap: ", unit_times_alap)

    ### Generate ILP file
    # we can generate this line by line using the graph
    # generated_ilp = ["Minimize", "2a1 + 2a2 + 3a3 + 5a4", "Subject To", "e0: x01 = 1", "...", "Integer", "a1 a2 a3 a4", "End"]
    ## minimize funciton
    ## execution, resource, and dependency constraints
    ## closing part
    ## write list
    generated_ilp = [] 
    generate_min_func(unit_cost, generated_ilp)
    generate_exec_cstrs(graph, unit_times_asap, unit_times_alap, generated_ilp)
    generate_rsrc_cstrs(graph, node_unit, unit_cost, schedule_obj, unit_times_asap, unit_times_alap, generated_ilp)
    generate_dep_cstrs(graph, unit_times_asap, unit_times_alap, generated_ilp)
    generate_closing(unit_cost, generated_ilp)
    write_list(ilp_filename, generated_ilp)

    # NOTE might need more constraints? test and confirm
    
    # TODO run ILP solver glpk command with os/subprocess.run() to generate the schedule
    # ex. ./glpsol --cpxlp 'ilp_filename'

    # TODO parse the scheduler output and display it nicely back to the user (QoR - Quality of Results)
    # if time allows, generate a graph like in fig 1.

    # TODO Final things: clean up comments, remove unused code, clean documentaiton, README
    # follow assignment requirements: correct directories, test/example scripts to show case features


def get_node_unit_cost(graph):
    '''
        Determine all the nodes and their associated units and costs.
    '''
    node_unit = {}
    unit_cost = {}
    for edge in graph.edges(data=True):
        root = edge[0]
        child = edge[1]
        e_attr = edge[2]
        root_unit = e_attr['root']
        child_unit = e_attr['child']
        root_cost = e_attr['root_cost']
        child_cost = e_attr['child_cost']
        node_unit[root] = root_unit
        node_unit[child] = child_unit
        unit_cost[root_unit] = root_cost
        unit_cost[child_unit] = child_cost
    node_unit = dict(sorted(node_unit.items()))
    unit_cost = dict(sorted(unit_cost.items()))
    return node_unit, unit_cost

    
def generate_min_func(unit_cost, generated_ilp, var_letter='a'):
    '''
        Generates the minimize funciton part of an ILP file using 
        the given unit costs and writes it to the given ilp list.
        \nex. "Minimize\n  2a1 + 2a2 + 3a3 + 5a4"
    '''
    # ex. "  2a1 + 2a2 + 3a3 + 5a4"
    min_func = [f"{cost}{var_letter}{unit}" for unit, cost in list(unit_cost.items())[1:-1]] # ignore source and sink
    min_func = "  " + " + ".join(x for x in min_func)
    generated_ilp.append("Minimize")
    generated_ilp.append(min_func)
    


def get_asap(graph):
    '''
        Get the ASAP unit times for the given graph.
        \nex. {'s': 0, 'v1': 1, 'v4': 2, 'v7': 3, ...}
    '''
    unit_times_asap = {}
    seen = set()

    level = 0
    s = list(graph.nodes())[0] # source node (assumes is first node)
    unit_times_asap[s] = level
    seen.add(s)

    children = sorted(list(graph.adj[s]))
    if not children:
        raise Exception('Invalid DFG, there are no children connected to source.')
    for child in children:
        dfs(graph, child, unit_times_asap, seen, level)

    # error check: make sure all the nodes have been seen from source
    if len(graph.nodes()) != len(seen):
        raise Exception('Invalid DFG, there is at least one node that is untraversable from source.')
    
    return unit_times_asap


def dfs(graph, node, unit_times, seen, level):
    '''
        Does a depth first search for the given graph and determines the time a node/unit executes.
        Recursively calls itself and keeps track of the node level. Updates the 'unit_times'
        dict and 'seen' set.
    '''
    level += 1
    n_level = unit_times.get(node, -1)
    if level > n_level:
        unit_times[node] = level
    seen.add(node)
    children = sorted(list(graph.adj[node]))
    for child in children:
        dfs(graph, child, unit_times, seen, level)


def get_alap(graph, latency_cstr):
    '''
        Get the ALAP unit times for the given graph.
        \nex. {'t': 5, 'v6': 4, 'v3': 3, 's': 0, ...}
    '''
    unit_times_alap = {}
    seen = set()

    level = latency_cstr + 1 # sink node is one level above
    t = list(graph.nodes())[-1] # sink node
    unit_times_alap[t] = level
    seen.add(t)

    parents = sorted(list(graph.predecessors(t)))
    if not parents:
        raise Exception('Invalid DFG, there are no parents connected to sink.')
    for parent in parents:
        dfs_reverse(graph, parent, unit_times_alap, seen, level)

    # error check: make sure all the nodes have been seen sink
    if len(graph.nodes()) != len(seen):
        raise Exception('Invalid DFG, there is at least one node that is untraversable from sink.')

    return unit_times_alap


def dfs_reverse(graph, node, unit_times, seen, level):
    '''
        Does a depth first search for the given graph and determines the time a node/unit executes.
        Recursively calls itself and keeps track of the node level. Updates the 'unit_times'
        dict and 'seen' set.
    '''
    level -= 1
    n_level = unit_times.get(node, float('inf'))
    if level < n_level:
        unit_times[node] = level
    seen.add(node)
    parents = sorted(list(graph.predecessors(node)))
    for parent in parents:
        dfs_reverse(graph, parent, unit_times, seen, level)


def generate_exec_cstrs(graph, unit_times_asap, unit_times_alap, generated_ilp, var_letter='x', cstr_var_letter='e'):
    '''
        Generate execution constraints for both ml-rc and mr-lc graphs.
        \nex. "  e0: x01 = 1" or "  e3: x31 + x32 + x33 = 1"
    '''
    # 'Subject To' part
    generated_ilp.append("Subject To")
    nodes = get_nodes(graph)
    for id, node in enumerate(nodes):
        id = 'n' if node == 't' else id
        start_time = unit_times_asap[node]
        end_time = unit_times_alap[node]
        exec_cstr = []
        for time in range(start_time, end_time + 1):
            exec_cstr.append(f"{var_letter}{id}{time}")

        # ex. "  e0: x01 = 1" or "  e3: x31 + x32 + x33 = 1"
        exec_cstr = " + ".join(x for x in exec_cstr)
        line = f"  {cstr_var_letter}{id}: {exec_cstr} = 1"
        generated_ilp.append(line)


def get_nodes(graph):
    '''
        Sort the nodes then remove/reinsert the source and sink (assumed to be first and last node). 
        Useful so that constraints can be added in the correct order.
    '''
    s = list(graph.nodes())[0] # source node (assumes is the first node)
    t = list(graph.nodes())[-1] # sink node (assumes is the last node)
    nodes = sorted(list(graph.nodes()))
    nodes.remove(s)
    nodes.remove(t)
    nodes.insert(0, s)
    nodes.append(t)
    return nodes


def generate_rsrc_cstrs(graph, node_unit, unit_cost, schedule_obj, unit_times_asap, unit_times_alap, generated_ilp, var_letter='x', cstr_var_letter='r', rsrc_var_letter='a'):
    '''
        Generate resource constraints for both ml-rc and mr-lc graphs.
        \nex. "  r0: x42 - a1 <= 0" or "  r3: x11 + x21 - a3 <= 0"
    '''
    # TODO: handle schedule ml-rc vs mr-lc
    # MR-LC
    cstr_id = 0
    nodes = get_nodes(graph)
    for unit, _ in list(unit_cost.items())[1:-1]:# ignore source and sink
        nodes_unit = [n for n, u in node_unit.items() if unit == u]
        for time in range(1, unit_times_asap['t']):
            rsrc_cstr = []
            for node in nodes_unit:
                start_time = unit_times_asap[node]
                end_time = unit_times_alap[node]
                if time >= start_time and time <= end_time:
                    rsrc_cstr.append(f"{var_letter}{nodes.index(node)}{time}")
            if rsrc_cstr:
                # ex. "  r0: x42 - a1 <= 0" or "  r3: x11 + x21 - a3 <= 0"
                rsrc_cstr = " + ".join(x for x in rsrc_cstr)
                line = f"  {cstr_var_letter}{cstr_id}: {rsrc_cstr} - {rsrc_var_letter}{unit} <= 0"
                cstr_id += 1
                generated_ilp.append(line) 
            #print("rsrc_cstr: ", rsrc_cstr)


def generate_dep_cstrs(graph, unit_times_asap, unit_times_alap, generated_ilp, var_letter='x', cstr_var_letter='d'):
    '''
        Generate dependency constraints for both ml-rc and mr-lc graphs.
        \nex. "  d0: 3x53 + 2x52 - 2x22 - 1x21 >= 1"
    '''
    
    # add all the node constraints
    cstr_id = 0
    nodes = get_nodes(graph)
    for id, node in enumerate(nodes):
        id = 'n' if node == 't' else id

        parents = sorted(list(graph.predecessors(node)))
        s = nodes[0] # source node (assumes is the first)
        if not parents or parents[0] == s: # source dependencies are implicit from execution constraints
            continue
        
        # compute node slack
        start_time = unit_times_asap[node]
        end_time = unit_times_alap[node]
        slack = end_time - start_time

        # compute parent slacks
        for parent in parents:
            parent_start_time = unit_times_asap[parent]
            parent_end_time = unit_times_alap[parent]
            parent_slack = parent_end_time - parent_start_time

            if slack or parent_slack: # dependencies on critical path are implicit from execution constraints
                # parent exec times
                dep_cstr = []
                for time in range(start_time, end_time + 1):
                    dep_cstr.append(f"{time}{var_letter}{id}{time}")
                plus_count = len(dep_cstr) - 1

                # parent exec times
                for time in range(parent_start_time, parent_end_time + 1):
                    parent_id = nodes.index(parent)
                    dep_cstr.append(f"{time}{var_letter}{parent_id}{time}") 
                
                # ex. "  d0: 3x53 + 2x52 - 2x22 - 1x21 >= 1"
                dep_cstr = " - ".join(x for x in dep_cstr)
                dep_cstr = dep_cstr.replace('-', '+', plus_count)
                line = f"  {cstr_var_letter}{cstr_id}: {dep_cstr} >= 1"
                cstr_id += 1
                generated_ilp.append(line)
    

def generate_closing(unit_cost, generated_ilp, var_letter='a'):
    '''
        Generates the closing part of an ILP file.
        \nex. "Integer\n  a1 a2 a3 a4\nEnd"
    '''
    generated_ilp.append("Integer")
    closing = [f"{var_letter}{unit}" for unit, _ in list(unit_cost.items())[1:-1]] # ignore source and sink
    closing = "  " + " ".join(x for x in closing)
    generated_ilp.append(closing)
    generated_ilp.append("End")


def write_list(filename, list_strings):
    '''
       Takes a list of strings and writes them to a file line by line. 
    '''
    with open(filename, 'w') as f:
        for s in list_strings:
            f.write("%s\n" % s)


if __name__ == "__main__":
    main(sys.argv[1:])
