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
    #print(list(G.nodes(data=True)))
    #print(list(G.edges(data=True)))

    #test printing args
    #print(args)

    #ensure user inserts a graph
    if args.graph is None:
        print("please insert an edgelist graph using -g")

    #generate cases for which scheduling algorithm to use (MR-LC or ML-RC)
    #base case 
    if args.latency is None and args.area_cost is None:
        print("please insert a latency or area cost restaint using arguments -l or -a ")
    elif args.latency is not None and args.area_cost is None:
        print("1")
        ml_rc(G)
    elif args.latency is None and args.area_cost is not None:
        print("2")
        mr_lc(G)
    elif args.latency is not None and args.area_cost is not None:
        print("3")
        both(G)
    


def ml_rc(G):
    return

def mr_lc(G):
    return

def both(G):
    return


if __name__ == "__main__":
    main(sys.argv[1:])
