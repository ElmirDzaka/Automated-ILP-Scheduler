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
import random

def main(argv):
    """
    main:
    The main function calls all helper methods and runs the program.
    """
    graph = write_edgelist()
    nx.write_edgelist(graph, "./test.edgelist")

    print(list(graph.nodes(data=True)))
    
    nx.draw(graph)
    plt.show()


def write_edgelist():
    G = nx.DiGraph(schedule="ilp")

    # unit map
    # 0 - source
    # 1 - adder
    # 2 - shifter
    # 3 - alu
    # 4 - mult
    # 5 - sink

    #source
    G.add_node("s", unit=0)

    #T1
    G.add_node("v1", unit=3)
    G.add_node("v2", unit=3)
    G.add_node("v3", unit=4)

    #T2
    G.add_node("v4", unit=1)
    G.add_node("v5", unit=2)
    G.add_node("v6", unit=3)

    #T3
    G.add_node("v7", unit=4)
    G.add_node("v8", unit=4)

    #T4
    G.add_node("v9", unit=3)

    #sink
    G.add_node("t", unit=5)

    # connect edges

    # each unit has associate cost
    # alu - cost 2
    # mult - cost 2

    # we store root, child type and cost for each

    # unit map  / costs
    # 0 - source(s)     0
    # 1 - adder         2
    # 2 - shifter       2
    # 3 - alu           3
    # 4 - mult          5
    # 5 - sink(t)       0

    #source
    G.add_edge("s","v1", root=0, child=3, root_cost = 0, child_cost = 3)
    G.add_edge("s","v2", root=0, child=3, root_cost = 0, child_cost = 3)
    G.add_edge("s","v3", root=0, child=4, root_cost = 0, child_cost = 5)

    #v1
    G.add_edge("v1","v4", root=3, child=1, root_cost = 3, child_cost = 2)

    #v2
    G.add_edge("v2","v5", root=3, child=2, root_cost = 3, child_cost = 2)
    G.add_edge("v2","v8", root=3, child=4, root_cost = 3, child_cost = 5)

    #v3
    G.add_edge("v3","v6", root=4, child=3, root_cost = 5, child_cost = 3)

    #v4
    G.add_edge("v4","v8", root=1, child=4, root_cost = 2, child_cost = 5)
    G.add_edge("v4","v7", root=1, child=4, root_cost = 2, child_cost = 5)

    #v5
    G.add_edge("v5","v9", root=2, child=3, root_cost = 2, child_cost = 3)

    #v6
    G.add_edge("v6","t", root=3, child=5, root_cost = 3, child_cost = 0)

    #v7
    G.add_edge("v7","t", root=4, child=5, root_cost = 5, child_cost = 0)

    #v8
    G.add_edge("v8","v9", root=4, child=3, root_cost = 5, child_cost = 3)

    #v9
    G.add_edge("v9","t", root=3, child=5, root_cost = 3, child_cost = 0)

    #sink
    
    #plt.figure(2)
    #nx.draw(G)
    #plt.show()

    return G
    

def generate_graphs(name, size):
    #size=int(sys.argv[-1])
    #name=str(sys.argv[-2])
    G=nx.gnp_random_graph(size,0.5,directed=True, seed=random.seed())
    DAG = nx.DiGraph([(u,v,{'weight':random.randint(1,10)}) for (u,v) in G.edges() if u<v])
    print(list(DAG))
    print(list(DAG.edges(data=True)))
    leaf = ([x for x in DAG.nodes() if DAG.out_degree(x)==0 and DAG.in_degree(x)!=0])
    print(len(leaf))
    for ln in leaf:
        G.add_edge(ln, 10+1, weight=random.randint(1,10))
    leaf = ([x for x in G.nodes() if G.out_degree(x)==0 and G.in_degree(x)!=0])
    print(len(leaf))
    nx.write_edgelist(DAG, name, data=["weight"])
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(G)
    plt.figure(1)
    nx.draw_networkx(G, node_color ='green', pos=nx.spectral_layout(G))
    plt.show()


if __name__ == "__main__":
    main(sys.argv[1:])
