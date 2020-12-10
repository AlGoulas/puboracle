#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import Counter
import itertools
from tqdm import tqdm

from igraph import Graph

def construct_edges_list(list_unique_items, 
                         list_coitems = None,
                         exclude = []):
    '''
    Input
    -----
    list_unique_items: list of unique items to serve as nodes of the network 
            to be constructed
     
    list_coitems: list of lists, with list_items[i] containing a list of "co-occuring"
            items. A connection will be placed in the network between them.
        
    exclude: list of str, default [], containing str that will function 
            as filter e.g., ['', ' '] 
    
    Output
    ------
    all_edges: list of tuples (i,j) denoting an edge between nodes i and j
    
    Note: there can be multiple such edges, e.g., (3,5) (3,5) (5,3),
    the sum of each unique pair denotes the strength of the association
    between i,j
    '''           
    all_edges = []
    # Iterate list_coitems - it is a list of of list of str
    #print(' Calculating network edges...')
    pbar = tqdm(total=len(list_coitems))
    pbar.set_description('Calculating network edges...') 
    for counter, current_coitems in enumerate(list_coitems):
        #Remove potential empty str and whitespaces
        current_coitems = [cci for cci in current_coitems if not cci.isspace() and cci]# "and cci" is checking if the string is not empty 
        # Remove strs if exclude is not empty
        # Changed is not None to the bool value of a list
        if exclude:
            current_coitems = [cci for cci in current_coitems if cci not in exclude]   
        # Get the indexes of each coauthor in the co_authors list
        # These indexes will be vertices indexes for network
        items_idx = [list_unique_items.index(cci) for cci in current_coitems]
        # Make pairs of indices between co-authors
        all_pairs = list(itertools.combinations(items_idx, 2))
        if len(all_pairs) > 1:
            all_edges.extend(all_pairs) 
        pbar.update(1)    
    pbar.close()
        
    return all_edges

def create_network_from_edge_wei_list(all_edges,
                                      nr_vertices = None,
                                      labels = None,
                                      directed = False,
                                      multiple = True,
                                      loops = False, 
                                      combine_edges = 'mean'):
    '''
    Create a igraph object from the list of edges all_edges
    
    Input
    -----
    all_edges: list of tuples of int specifying pairs of nodes (each a unique 
        int) that are connected (returned from construct_edges_list)
    
    nr_vertices: int, default None, a positive integer specyfying the number 
        of vertices in the graph
        
    labels: a list of str of len == nr_vertices containing the labels of each
        vertex
        
    directed: bool, default False, specyfying if the graph is directed

    multiple: bool, default True, allow multiple edges to exist in the graph

    loops: bool, default False, allow self-self conenctions

    combine_edges: str, default 'mean', specyfying how edge wweights are 
        combined when simplifying the graph
        See https://igraph.org/python/doc/igraph.GraphBase-class.html#simplify 
        
    
    Output
    ------
    net: igraph object
    '''
    net = Graph(directed = directed)
    net.add_vertices(nr_vertices)
    
    # Create a counter object that summarizes unique edges and their occurence
    # The edge occurence is treated a the edge weight
    counted_edges = Counter(all_edges)
    edges = [pair for pair in counted_edges.keys()] # list of tuples (unique edges)
    weights = [wei for wei in counted_edges.values()] # list of weights
    
    # Add edges and respective weights to the graph
    net.add_edges(edges)
    net.es['weight'] = weights

    # Construct the graph with or without loops (self-self connections) and 
    # multiple edges and combine edges based on the combine_edges str param 
    net.simplify(multiple = multiple, 
                 loops = loops, 
                 combine_edges = combine_edges
                 )
    # Add the unique_items as labels to the igraph object
    net.vs['label'] = labels
    
    return net
