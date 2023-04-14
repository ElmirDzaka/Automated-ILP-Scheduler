"""
Authors:
Elmir Dzaka
Kidus Yohannes

Summary:
This file takes in an edgelist graph and processes it using NetworkX.

"""
import sys
import networkx as nx
import matplotlib.pyplot as plt
import argparse

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

    G = nx.read_edgelist(args.graph)
    print(list(G.nodes(data=True)))
    print(list(G.edges(data=True)))

    
    
if __name__ == "__main__":
    main(sys.argv[1:])
