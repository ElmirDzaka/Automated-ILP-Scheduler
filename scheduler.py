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
    input_file = str(argv[0])
    print(input_file)

    g_input = nx.read_edgelist(input_file)
    print(g_input.nodes["v1"])
    
    exit()

    graph = write_edgelist();
    nx.write_edgelist(graph, "./test.edgelist");

    #print(nx.info(graph))
    print(graph.nodes["v1"])
    
    nx.draw(graph)
    plt.show()


def write_edgelist():
    G = nx.DiGraph()
    #add nodes from the example DFG

    #source
    G.add_node("s", type_="source")

    #T1
    G.add_node("v1", type_="alu")
    G.add_node("v2", type_="alu")
    G.add_node("v3", type_="mult")

    #T2
    G.add_node("v4", type_="alu")
    G.add_node("v5", type_="shifter")
    G.add_node("v6", type_="alu")

    #T3
    G.add_node("v7", type_="mult")
    G.add_node("v8", type_="mult")

    #T4
    G.add_node("v9", type_="alu")

    #sink
    G.add_node("t", type_="sink")

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
