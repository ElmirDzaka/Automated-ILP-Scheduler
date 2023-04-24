"""
Authors:
Elmir Dzaka
Kidus Yohannes

Summary:
This file takes in an edgelist graph and and automatically generates the schedule using ILP solver GLPK,
and produces the Quality-of-Results. Supports ML-RC, MR-LC, or both using Pareto-optimal analysis.

Start date: 4/3/2023
Last updated: 4/18/2023
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

    parser.add_argument('-l', '--latency', type=int, help="The desired latency to minimize memory under.")      # option that takes a value
    parser.add_argument('-a', '--area_cost', type=int, help="The desired area cost to minimize latency under.")      # option that takes a value
    parser.add_argument('-g', '--graph', type=argparse.FileType('r'), help="The desired DFG to automate the schedule for using ILP. It should be in edgelist format.")      # option that takes a value
    args = parser.parse_args()           

    # ensure user inserts a graph
    if args.graph is None:
        print("please insert an edgelist graph using -g")
        exit()

    graph = nx.read_edgelist(args.graph, create_using=nx.DiGraph)

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
    var_letter = 'a'
    unit_costs = generateMinFunc(graph, generated_ilp, var_letter)
    print(f"unit_costs: {unit_costs}")

    #
    # TODO generate execution constraints
    #
    generateExecFunc(graph, generated_ilp)
    #
    # TODO generate resource constraints (handle accordingly depending on ML-RC or MR-LC)
    #

    #
    # TODO generate dependency constraints
    #

    # generate closing part
    generateClosing(generated_ilp, unit_costs, var_letter)


    write_list(ilp_filename, generated_ilp)

    # TODO be sure to catch/determine any infeasibilties of the graph/ILP

    # TODO run ILP solver glpk command with os/subprocess.run() to generate the schedule
    # ex. ./glpsol --cpxlp 'ilp_filename'

    # TODO parse the scheduler output and display it nicely back to the user (QoR - Quality of Results)
    # if time allows, generate a graph like in fig 1.

    # TODO Final things: clean up comments, remove unused code, clean documentaiton, README
    # follow assignment requirements: correct directories, test/example scripts to show case features


# generate execution constraints for both ml-rc and mr-lc graphs
def generateExecFunc(graph, generated_ilp):
    #TODO implement DPS for ASAP and ALAP and generate exec func (probably create helper for DPS)c
    unit_times = {}
    seen = set()

    # TODO error check: make sure there is not a cycle

    # Get the unit times for ASAP
    s = list(graph.nodes())[0] # source node
    unit_times[s] = 0
    seen.add(s)
    children = sorted(list(graph.adj[s]))
    if not children:
        raise Exception('Invalid DFG, there are no children connected to source.')
    for child in children:
        dfs(graph, child, unit_times, seen)
    unit_time_asap = unit_times
    print(unit_time_asap)

    # TODO: error check: make sure all the nodes have been seen

    #
    # TODO: Get the unit times for ASAP
    #

    # generate execution constraints


def dfs(graph, node, unit_times, seen, level=0):
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


def generateMinFunc(graph, generated_ilp, var_letter):
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
    

def generateClosing(generated_ilp, unit_costs, var_letter):
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
