"""
Authors:
Elmir Dzaka
Kidus Yohannes

Summary:
This file takes in an edgelist graph and and automatically generates the schedule using ILP solver GLPK,
and produces the Quality-of-Results. Supports ML-RC, MR-LC, or both using Pareto-optimal analysis.

Start date: 4/3/2023
Last updated: 4/24/2023
"""
import sys
import argparse
import networkx as nx


def main(argv):
    """
    main:
    The main function calls all helper methods and runs the program.
    """
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
    elif args.latency and args.area_cost is None:
        schedule_obj = "ML-RC"
    elif args.latency is None and args.area_cost:
        schedule_obj = "MR-LC"
    elif args.latency and args.area_cost:
        schedule_obj = "both"
        # TODO read/determine what pareto-optimal analysis using both results looks like
    
    print(f"schedule: {schedule_obj}")
    ilp_filename = f"auto_{schedule_obj}.ilp" 
    
    #
    # Generate ILP 
    #
    generated_ilp = []
    # ex. we can generate this line by line using the graph
    # generated_ilp = ["Minimize", "2a1 + 2a2 + 3a3 + 5a4", "Subject To", "e0: x01 = 1", "...", "Integer", "a1 a2 a3 a4", "End"]

    # generate minimize function
    unit_costs = generate_min_func(graph, generated_ilp)
    print(f"unit_costs: {unit_costs}")

    # generate execution constraints
    generateExecFunc(graph, args.latency, generated_ilp)

    #
    # TODO generate resource constraints (handle accordingly depending on ML-RC or MR-LC)
    #

    #
    # TODO generate dependency constraints
    #

    # generate closing part
    generate_closing(unit_costs, generated_ilp)

    write_list(ilp_filename, generated_ilp)

    # TODO be sure to catch/determine any infeasibilties of the graph/ILP

    # TODO run ILP solver glpk command with os/subprocess.run() to generate the schedule
    # ex. ./glpsol --cpxlp 'ilp_filename'

    # TODO parse the scheduler output and display it nicely back to the user (QoR - Quality of Results)
    # if time allows, generate a graph like in fig 1.

    # TODO Final things: clean up comments, remove unused code, clean documentaiton, README
    # follow assignment requirements: correct directories, test/example scripts to show case features


# generate execution constraints for both ml-rc and mr-lc graphs
def generateExecFunc(graph, latency, generated_ilp, var_letter='x', cstr_var_letter='c'):

    # TODO error check: make sure there is not a cycle

    # first get the unit times for ASAP and ALAP
    unit_times_asap = get_asap(graph)

    t = list(graph.nodes())[-1] # sink node
    asap_latency_cstr = unit_times_asap[t] - 1 # the level before sink is the time of the last unit exec
    latency_cstr = latency if latency else asap_latency_cstr # either from user supplied latency constraint or ASAP
    if latency < asap_latency_cstr: # error check: make sure latency isn't too small
        raise Exception(f'Solution not posible, given latency constraint is too small. Should be at least {asap_latency_cstr}.')
    
    unit_times_alap = get_alap(graph, latency_cstr)
    
    print("asap: ", unit_times_asap, "\nalap: ", unit_times_alap)

    # generate the execution constraints

    # 'Subject To' part
    generated_ilp.append("Subject To")

    # add source constraint
    id = time = 0
    exec_func = f"{var_letter}{id}{time}"
    line = f"  {cstr_var_letter}{id}: {exec_func} = 1"
    generated_ilp.append(line)

    # first sort and remove source and sink so nodes are iterated in order
    nodes = sorted(list(graph.nodes()))
    nodes.remove('s')
    nodes.remove('t')

    # add all the node constraints
    for id, node in enumerate(nodes):
        id += 1 # have index start at 1 because source was removed
        start_time = unit_times_asap[node]
        end_time = unit_times_alap[node]
        exec_vars = []
        for time in range(start_time, end_time + 1):
            exec_vars.append(f"{var_letter}{id}{time}")

        # ex. "  e0: x01 = 1" "  e3: x31 + x32 + x33 = 1"
        exec_func = " + ".join(v for v in exec_vars)
        line = f"  {cstr_var_letter}{id}: {exec_func} = 1"
        generated_ilp.append(line)

    # add sink constraint
    id = 'n'
    time = latency_cstr + 1 # the time for sink is one more then the last unit exec
    exec_func = f"{var_letter}{id}{time}"
    id = len(graph.nodes) - 1 # constraint ids start at 0
    line = f"  {cstr_var_letter}{id}: {exec_func} = 1"
    generated_ilp.append(line)


def get_asap(graph):
    '''
        Get the ASAP unit times for the given graph.
    '''
    unit_times_asap = {}
    seen = set()

    level = 0
    s = list(graph.nodes())[0] # source node
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


def get_alap(graph, latency_cstr):
    '''
        Get the ALAP unit times for the given graph.
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


def generate_min_func(graph, generated_ilp, var_letter='a'):
    '''
        Generates the minimize funciton part of an ILP file using the given networkx graph, 
        writes it to the given ilp list and returns the unit costs.
    '''
    # determine all the units and their associated costs
    unit_costs = {}
    for edge in graph.edges(data=True):
        e_attr = edge[2]
        root = e_attr['root']
        child = e_attr['child']
        root_cost = e_attr['root_cost']
        child_cost = e_attr['child_cost']
        unit_costs[root] = root_cost
        unit_costs[child] = child_cost
    unit_costs = sorted(unit_costs.items())
    
    #min_func = ["2a1", "2a2", "3a3", "5a4"]
    min_func = [f"{cost}{var_letter}{unit}" for unit, cost in unit_costs[1:-1]] # ignore source and sink
    # ex. "  2a1 + 2a2 + 3a3 + 5a4"
    min_func = "  " + " + ".join(x for x in min_func)
    generated_ilp.append("Minimize")
    generated_ilp.append(min_func)
    return unit_costs
    

def generate_closing(unit_costs, generated_ilp, var_letter='a'):
    '''
        Generates the closing part of an ILP file.
    '''
    generated_ilp.append("Integer")
    closing = [f"{var_letter}{unit}" for unit, _ in unit_costs[1:-1]] # ignore source and sink
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
