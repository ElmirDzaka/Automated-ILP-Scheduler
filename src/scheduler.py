"""
Authors:
Elmir Dzaka
Kidus Yohannes

Summary:
    This file takes in an edgelist graph and and automatically generates the schedule using ILP solver GLPK
    and produces the Quality-of-Results. Supports ML-RC, MR-LC, or both using Pareto-optimal analysis.

Start date: 4/3/2023
Last updated: 5/3/2023
"""
import sys
import argparse
import os
import networkx as nx
from tabulate import tabulate


def main(argv):
    """
        Starting point for the program.
    """
    parser = argparse.ArgumentParser(
                    prog='Automated ILP Scheduler',
                    description='Automatically generates the schedule and produces the QoRs of the schedule for the given DFG graph. Interfaces with LPKSolver.',
                    epilog='Developed by Elmir and Kidus :cool emoji:')

    parser.add_argument('-l', '--latency', type=int, help="The desired latency to minimize memory under.")
    parser.add_argument('-a', '--area_cost', type=int, nargs='+', help="The desired area cost to minimize latency under. Input as a space seperated list of integers.")
    parser.add_argument('-g', '--graph', type=argparse.FileType('r'), help="The desired DFG to automate the schedule for using ILP. It should be in edgelist format.")
    args = parser.parse_args()

    # ensure user inserts a graph
    if args.graph is None:
        print("please insert an edgelist graph using -g")
        exit()

    graph = nx.read_edgelist(args.graph, create_using=nx.DiGraph) # assumes first and last node are source and sink

    # generate cases for which scheduling algorithm to use (MR-LC or ML-RC)
    if args.latency is None and args.area_cost is None:
        print("please insert a latency or area cost restraint using arguments -l or -a ")
        exit()
    elif not args.latency and args.area_cost:
        schedule_obj = "ML-RC"
    elif args.latency and not args.area_cost:
        schedule_obj = "MR-LC"
    elif args.latency and args.area_cost:
        schedule_obj = "both" 
    
    # run scheduler based on chosen objective
    if schedule_obj == "ML-RC" or schedule_obj == "MR-LC":
        run_scheduler(schedule_obj, graph, args)
    # TODO read/determine what pareto-optimal analysis using both results looks like
    elif schedule_obj == "both":
        run_scheduler("ML-RC", graph, args)
        run_scheduler("MR-LC", graph, args)
    

def run_scheduler(schedule_obj, graph, args):
    '''
        Runs the entire scheduler based on the given schedule objective (ML-RC or MR-LC), graph and args.
    '''
    print(f"schedule: {schedule_obj}")
    lp_filename = rf"auto_{schedule_obj}.lp" 
    
    # error check: make sure there is not a cycle
    visited = rec_stack = dict.fromkeys(sorted(graph), False)
    for node in graph.nodes():
        if is_cyclic(graph, node, visited, rec_stack):
            raise Exception('Invalid DFG, there is a cycle detected in the graph.')

    # parse graph and get node units and costs
    node_unit, unit_cost = get_node_unit_cost(graph)
    print("node units:", node_unit)
    print(f"unit_costs: {unit_cost}")

    # ensure user inserts the right amount of area constraints
    if args.area_cost and len(unit_cost) - 2 != len(args.area_cost):
        raise Exception(f'Expected {len(unit_cost) - 2} area constraints but only {len(args.area_cost)} supplied.')

    # get the unit times for ASAP and ALAP
    unit_times_asap = get_asap(graph)

    t = list(graph.nodes())[-1] # sink node (assumes is the last node)
    asap_latency_cstr = unit_times_asap[t] - 1 # the level before sink is the time of the last unit exec
    latency_cstr = args.latency if args.latency else asap_latency_cstr # either from user supplied latency constraint or ASAP
    if latency_cstr < asap_latency_cstr: # error check: make sure latency isn't too small
        raise Exception(f'Solution not posible, given latency constraint is too small. Should be at least {asap_latency_cstr}.')
    unit_times_alap = get_alap(graph, latency_cstr)
    print("asap: ", unit_times_asap, "\nalap: ", unit_times_alap)

    ### generate ILP file, we can generate this line by line using the graph
    # ex. generated_ilp = ["Minimize", "2a1 + 2a2 + 3a3 + 5a4", "Subject To", "e0: x01 = 1", "...", "Integer", "a1 a2 a3 a4", "End"]
    generated_ilp = []
    integer_set = []
    crit_path_nodes = []
    generated_ilp.append("Minimize")
    generate_min_func(schedule_obj, graph, unit_times_asap, unit_times_alap, unit_cost, integer_set, crit_path_nodes, generated_ilp)
    generated_ilp.append("Subject To")
    generate_exec_cstrs(graph, unit_times_asap, unit_times_alap, generated_ilp)
    generate_rsrc_cstrs(schedule_obj, graph, unit_cost, node_unit, args.area_cost, unit_times_asap, unit_times_alap, generated_ilp)
    generate_dep_cstrs(graph, unit_times_asap, unit_times_alap, generated_ilp)
    generate_closing(schedule_obj, integer_set, unit_cost, generated_ilp)
    write_list(lp_filename, generated_ilp)

    # run ILP solver (GLPK command) and output the text file
    # ex. ./glpsol --cpxlp 'lp_filename'
    glpsol_dir = r"../../glpk-4.35/examples/glpsol" # NOTE: assumes glpk dir is two directories up (same dir as the repo)
    output_txt = f"{lp_filename[:-3]}.txt"
    os.system(rf"{glpsol_dir} --cpxlp {lp_filename} -o {output_txt} >/dev/null 2>&1")

    # parse the output and save it into a dict
    min_results = {"obj": 0, "counts": {}}
    with open(output_txt) as file:
        for line in file:
            line = line.split()
            if line and line[0] == 'Objective:':
                min_results["obj"] = line[3]
            elif len(line) == 5 and line[2] == '*':
                min_results["counts"][line[1]] = line[3]            
    
    # display the results nicely back to the user (QoR - Quality of Results)
    if schedule_obj == "ML-RC":
        data = []
        for node in crit_path_nodes: # show critical path nodes first
            data.append([node, unit_times_asap[node]])
        for unit, count in min_results['counts'].items():
            if int(count) == 1:
                unit = unit.split("_")
                node_id = int(unit[1])
                cycle = unit[2]
                data.append([get_nodes(graph)[node_id], cycle])
        min_latency = max([int(x[1]) for x in data])
        print(f"The minimized latency is {min_latency}.")
        print("Here is each node with its optimized cycle:")
        print(tabulate(data, headers = ["Node", "Cycle"]))
    elif schedule_obj == "MR-LC":
        print(f"The minimized area is {min_results['obj']}.")
        print("Here is each resource with its optimized count:")
        data = [[unit, count] for unit, count in min_results['counts'].items()]
        print(tabulate(data, headers = ["Resource", "Min Count"]))


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


def is_cyclic(graph, node, visited, rec_stack):
    '''
        Checks if there is a cycle in the given graph.
        Keeps track of visited nodes and ones on the recursive stack.
        If a node is seen that is already in the recursive stack, then
        that means there is a cycle.
    '''
    if rec_stack[node]: # if node was already seen in recursive stack
        return True
    if visited[node]: # node has already been seen
        return False
    visited[node] = rec_stack[node] = True

    children = sorted(list(graph.adj[node]))
    for child in children:
        if is_cyclic(graph, child, visited, rec_stack):
            return True
            
    rec_stack[node] = False # remove node from recursion stack before function ends
    return False # no cycle exists


def generate_min_func(schedule_obj, graph, unit_times_asap, unit_times_alap, unit_cost, integer_set, crit_path_nodes, generated_ilp, ml_var_letter='x', mr_var_letter='a'):
    '''
        Generates the minimize funciton part of an ILP file using 
        the given unit costs and writes it to the given ilp list depending
        on the schedule_obj.
        \nML-RC ex. "  1x21 + 2x22 + 1x31 + 2x32 + 3x33 + 2x52 + 3x53 + 2x62 + 3x63 + 4x64 + 3x73 + 4x74
        \nMR-LC ex. "  2a1 + 2a2 + 3a3 + 5a4"
    '''
    s = list(graph.nodes())[0] # source node (assumes is the first node)
    t = list(graph.nodes())[-1] # sink node (assumes is the last node)
    if schedule_obj == "ML-RC":
        min_func = []
        nodes = get_nodes(graph)
        for id, node in enumerate(nodes):
            id = 'n' if node == t else id 
            start_time = unit_times_asap[node]
            end_time = unit_times_alap[node]
            if start_time == end_time: # on critical path, redundant to include
                if node != s and node != t: # ignore source and sink node
                    crit_path_nodes.append(node)
                continue
            else:
                for time in range(start_time, end_time + 1):
                    min_func.append(f"{time}{ml_var_letter}_{id}_{time}")
                    integer_set.append(f"{ml_var_letter}_{id}_{time}")
        min_func = "  " + " + ".join(x for x in min_func)
        generated_ilp.append(min_func)
        return min_func

    elif schedule_obj == "MR-LC":
        # ex. "  2a1 + 2a2 + 3a3 + 5a4"
        min_func = [f"{cost}{mr_var_letter}{unit}" for unit, cost in list(unit_cost.items())[1:-1]] # ignore source and sink
        min_func = "  " + " + ".join(x for x in min_func)
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
    cstr_id = 0
    nodes = get_nodes(graph)
    for id, node in enumerate(nodes):
        id = 'n' if node == 't' else id
        start_time = unit_times_asap[node]
        end_time = unit_times_alap[node]
        exec_cstr = []
        for time in range(start_time, end_time + 1):
            exec_cstr.append(f"{var_letter}_{id}_{time}")

        # ex. "  e0: x01 = 1" or "  e3: x31 + x32 + x33 = 1"
        exec_cstr = " + ".join(x for x in exec_cstr)
        line = f"  {cstr_var_letter}{cstr_id}: {exec_cstr} = 1"
        generated_ilp.append(line)
        cstr_id += 1


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


def generate_rsrc_cstrs(schedule_obj, graph, unit_cost, node_unit, unit_count, unit_times_asap, unit_times_alap, generated_ilp, var_letter='x', cstr_var_letter='r', rsrc_var_letter='a'):
    '''
        Generate resource constraints for both ml-rc and mr-lc graphs.
        \nex. "  r0: x42 - a1 <= 0" or "  r3: x11 + x21 - a3 <= 0"
    '''
    cstr_id = 0
    nodes = get_nodes(graph)
    for unit, _ in list(unit_cost.items())[1:-1]:# ignore source and sink
        nodes_unit = [n for n, u in node_unit.items() if unit == u]
        if schedule_obj == "ML-RC":
            subtrahend = unit_count[unit - 1]
        elif schedule_obj == "MR-LC":
            subtrahend = f"{rsrc_var_letter}{unit}"
        for time in range(1, unit_times_alap['t']): # loop to latency constraint
            rsrc_cstr = []
            for node in nodes_unit:
                start_time = unit_times_asap[node]
                end_time = unit_times_alap[node]
                if time >= start_time and time <= end_time:
                    rsrc_cstr.append(f"{var_letter}_{nodes.index(node)}_{time}")
            if rsrc_cstr:
                # ex. "  r0: x42 - a1 <= 0" or "  r3: x11 + x21 - a3 <= 0"
                rsrc_cstr = " + ".join(x for x in rsrc_cstr)
                if schedule_obj == "MR-LC":
                    line = f"  {cstr_var_letter}{cstr_id}: {rsrc_cstr} - {subtrahend} <= 0"
                if schedule_obj == "ML-RC":
                    line = f"  {cstr_var_letter}{cstr_id}: {rsrc_cstr} <= {subtrahend}"
                generated_ilp.append(line)
                cstr_id += 1


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
                    dep_cstr.append(f"{time}{var_letter}_{id}_{time}")
                plus_count = len(dep_cstr) - 1

                # parent exec times
                for time in range(parent_start_time, parent_end_time + 1):
                    parent_id = nodes.index(parent)
                    dep_cstr.append(f"{time}{var_letter}_{parent_id}_{time}") 
                
                # ex. "  d0: 3x53 + 2x52 - 2x22 - 1x21 >= 1"
                dep_cstr = " - ".join(x for x in dep_cstr)
                dep_cstr = dep_cstr.replace('-', '+', plus_count)
                line = f"  {cstr_var_letter}{cstr_id}: {dep_cstr} >= 1"
                generated_ilp.append(line)
                cstr_id += 1
    

def generate_closing(schedule_obj, integer_set, unit_cost, generated_ilp, var_letter='a'):
    '''
        Generates the closing part of an ILP file, which depends on the number of units.
        \nex. "Integer\n  a1 a2 a3 a4\nEnd"
    '''
    if schedule_obj == "ML-RC":
        generated_ilp.append("Integer")
        integer_set = "  " + " ".join(x for x in integer_set)
        generated_ilp.append(integer_set)
        generated_ilp.append("End")
    elif schedule_obj == "MR-LC":
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
