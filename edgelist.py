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

def main(argv):
    """
    main:
    The main function calls all helper methods and runs the program.
    """
    graph = write_edgelist();

    print(nx.info(graph))
    nx.draw(graph)
    plt.show()


def write_edgelist():
    G = nx.Graph()
    #add nodes from the example DFG

    #source
    G.add_node("s")

    #T1
    G.add_node("v1")
    G.add_node("v2")
    G.add_node("v3")

    #T2
    G.add_node("v4")
    G.add_node("v5")
    G.add_node("v6")

    #T3
    G.add_node("v7")
    G.add_node("v8")

    #T4
    G.add_node("v9")

    #sink
    G.add_edge("t")

    #connect edges

    #source
    G.add_edge("s","v1")
    G.add_edge("s","v2")
    G.add_edge("s","v3")

    #v1
    G.add_edge("v1","v4")

    #v2
    G.add_edge("v2","v5")
    G.add_edge("v2","v8")

    #v3
    G.add_edge("v3","v6")

    #v4
    G.add_edge("v4","v8")
    G.add_edge("v4","v7")

    #v5
    G.add_edge("v5","v9")

    #v6
    G.add_edge("v6","t")

    #v7
    G.add_edge("v7","t")

    #v8
    G.add_edge("v8","v9")

    #v9
    G.add_edge("v9","t")

    #sink

    return G
    
    


if __name__ == "__main__":
    main(sys.argv[1:])
