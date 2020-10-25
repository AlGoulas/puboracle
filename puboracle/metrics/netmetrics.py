#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import itertools
import numpy as np

from igraph import Graph

def build_net_coauthors(list_unique_authors, list_coauthorships=None):
    '''
    BETA
    '''
    # Initialize the graph and as many verttices as len(list_unique_authors)
    g = Graph(len(list_unique_authors), directed=False)    
    first = True
    # Iterate list_coauthorships - it is a list of str
    # Each str contains all the co-authors seperated by ';'
    nr_coauthorships = len(list_coauthorships)
    for counter,current_coauthorships in enumerate(list_coauthorships):
        print('Iterating...:',counter, '/', nr_coauthorships)
        co_authors = current_coauthorships.split(';')
        
        # Get the indexes of each coauthor in the co_authors list
        # These indexes will be vertices indexes for network g
        author_idx = [list_unique_authors.index(ca) for ca in co_authors]
        
        # Make pairs of indices between co-authors
        # This contains double pairs, e.g., 1,2 2,1 which is reduntant for 
        # undirected graphs
        all_pairs = make_pairs_idx(author_idx)
        if all_pairs:
            all_weights = [1]*len(all_pairs)
            
            if first is True:
                g.add_edges(all_pairs)
                g.es['weight'] = all_weights
                first = False
            else:
                g = add_edges_to_graph(g, 
                                       edge_list = all_pairs, 
                                       weight_list = all_weights
                                       )
                    
    return g

def make_pairs_idx(list_idx, without_swaps=True):
    '''
    Create a list of tuples containing all the pairs i,j of integers contained 
    in list_idx without swaping pairs: (i,j) excludes (j,i) from the list
    
    Input
    -----
    list_idx: list of int out of which pairs will be contructed
    
    without_swaps: bool, default True, sepcifying if all_pairs should be 
        constructed with (i,j) but not (j,i) (=True) or with both
        (i,j) and (j,i) (=False)
        
    Output
    ------
    all_pairs: list of tuples of int pairs    
    '''
    if without_swaps is False:
        # Make the condition for adding the pair a lambda fun
        f = lambda i, j, all_pairs: (i,j) not in all_pairs and (j,i) not in all_pairs and i != j
        #Create the pairs from list_idx
        all_pairs = []
        for i in list_idx:
            pairs = [(i,j) for j in list_idx if f(i, j, all_pairs)]
            all_pairs.extend(pairs) 
    else:
        all_pairs = list(itertools.permutations(list_idx, 2))
        
    return all_pairs             
                
def add_edges_to_graph(g, 
                       edge_list = None, 
                       weight_list = None):
    '''
    BETA
    '''
    g_edges = g.get_edgelist()
    g_weight = g.es['weight']
    
    all_idx_remove = []
    for position,e in enumerate(edge_list):
        if g.are_connected(e[0], e[1]) is True:
            # We are working on an undirected graph, thus (i,j)=(j,i)
            try:
                idx_remove = g_edges.index(e)
            except:
                idx_remove = g_edges.index((e[1],e[0]))
             
            # If edge exists then add the existing weight to the new weight    
            g_weight[idx_remove] = g_weight[idx_remove] + weight_list[position]  
            all_idx_remove.append(idx_remove)# Save the idx for removing
    
    # Remove all_idx_remove from edge_list and weight_list
    edge_list = [item for i,item in enumerate(edge_list) if i not in all_idx_remove]  
    weight_list = [item for i,item in enumerate(weight_list) if i not in all_idx_remove] 
    
    # Update g with weights and edges
    g = Graph(g.vcount(), directed=False)#create new graph (something is off when "updating" the existing one)
    g.add_edges(g_edges + edge_list)
    g.es['weight'] = g_weight + weight_list
    
    return g

def build_net_coauthors_np(list_unique_authors, list_coauthorships=None):
    '''
    BETA
    '''
    # Initialize the graph and as many verttices as len(list_unique_authors)
    g = np.zeros((len(list_unique_authors), len(list_unique_authors)))   
    
    # Iterate list_coauthorships - it is a list of str
    # Each str contains all the co-authors seperated by ';'
    nr_coauthorships = len(list_coauthorships)
    for counter,current_coauthorships in enumerate(list_coauthorships):
        print('Iterating...:',counter, '/', nr_coauthorships)
        co_authors = current_coauthorships.split(';')
        
        if len(co_authors) > 1:
            # Get the indexes of each coauthor in the co_authors list
            # These indexes will be vertices indexes for network g
            author_idx = [list_unique_authors.index(ca) for ca in co_authors]
            
            # Make pairs of indices between co-authors
            all_pairs = np.asarray(make_pairs_idx(author_idx))
            
            # Update graph
            g[all_pairs[:,0], all_pairs[:,1]] = g[all_pairs[:,0], all_pairs[:,1]] + 1   
           
    return g

def construct_edge_wei_list(list_unique_authors, 
                            list_coauthorships = None,
                            exclude = []
                            ):
    '''
    Input
    -----
    list_unique_authors: list of str, with the unique str that will serve as
        the nodes of the network to be constructed
     
    list_coauthorships: list of str with the author names of a publication. 
        Each str potentially contains many ;-seperated author names 
        
    exclude: list of str, default [], containing str that will function as filter
      e.g., ['', ' '] 
      
    Output
    ------
    all_edges: list of tuples (i,j) denoting an edge between nodes i and j
        Note: there can be multiple such edges, e.g., (3,5) (3,5) (5,3),
        the sum of each unique pair denotes the strength of the association
        between i,j
    
    '''           
    all_edges = []
    # Iterate list_coauthorships - it is a list of str
    # Each str contains all the co-authors seperated by ';'
    nr_coauthorships = len(list_coauthorships)
    for counter,current_coauthorships in enumerate(list_coauthorships):
        print('Iterating...:',counter, '/', nr_coauthorships)
        co_authors = current_coauthorships.split(';')
        
        # Remove strs if exclude is not None
        if exclude is not None:
            co_authors = [ca for ca in co_authors if ca not in exclude]
        
        # Get the indexes of each coauthor in the co_authors list
        # These indexes will be vertices indexes for network
        author_idx = [list_unique_authors.index(ca) for ca in co_authors]
        
        # Make pairs of indices between co-authors
        # This contains double pairs, e.g., 1,2 2,1 which is reduntant for 
        # undirected graphs
        all_pairs = make_pairs_idx(author_idx)
        if len(all_pairs) > 1:
            all_edges.extend(all_pairs)
            
    return all_edges