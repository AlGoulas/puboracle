#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import Counter
import itertools
from tqdm import tqdm

from igraph import Graph

def _construct_edges_list(list_unique_items, 
                          list_coitems=None,
                          exclude=[]):
    '''
    Args:
        list_unique_items: list of unique items to serve as nodes of the network 
            to be constructed
     
        list_items: list of lists, with list_items[i] containing a list of "co-occuring"
            items. A conenction will be placed in the network between them.
        
        exclude: list of str, default [], containing str that will function 
            as filter e.g., ['', ' '] 
    
    Returns:
        all_edges: list of tuples (i,j) denoting an edge between nodes i and j
            Note: there can be multiple such edges, e.g., (3,5) (3,5) (5,3),
            the sum of each unique pair denotes the strength of the association
            between i,j
    '''           
    all_edges = []
    # Iterate list_coauthorships - it is a list of of list of str
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

def _create_network_from_edge_wei_list(all_edges,
                                       nr_vertices,
                                       directed=False,
                                       multiple=True,
                                       loops=False, 
                                       combine_edges='mean'):
    net = Graph(directed=directed)
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
    net.simplify(multiple=multiple, 
                 loops=loops, 
                 combine_edges=combine_edges
                 )
        
    return net, edges, weights

def compute_graph(pub_list, item='authors'):
    """
    Args:
        pub_list: list of Publication objects
        
        item: {'authors', 'affiliation'}, default 'authors', 
            where to create graph on
    Returns:
        net: an igraph object describing the relation between the items in the
            form of a graph. 
            Note that labels of each node are contained in:
            net.vs['label']
        
        co_items: the list of co-appearing items
    """
    co_items = []    
    pbar = tqdm(total=len(pub_list))
    pbar.set_description('Extracting '+ item)
    for pub in pub_list:
        # Make a co_author_list from the current pub object
        if item == 'authors':
            current_co_items = [author.forename + ' ' + author.lastname for author in pub.authors]
        if item == 'affiliations':    
            current_co_items = [affil.name for affil in pub.get_unique_affiliations()]
        co_items.append(current_co_items)
        pbar.update(1)    
    pbar.close()
    
    # Create edge list
    unique_items = list(set([x for sublist in co_items for x in sublist]))
    all_edges = _construct_edges_list(unique_items, 
                                      list_coitems=co_items,
                                      exclude=[]
                                      )
    
    # create igraph network
    (net, 
     _, 
     _) = _create_network_from_edge_wei_list(all_edges,
                                             nr_vertices = len(unique_items)
                                             )
    
    # Add the unique_items as labels to the igraph object
    net.vs['label'] = unique_items 
    
    return net, co_items           
                