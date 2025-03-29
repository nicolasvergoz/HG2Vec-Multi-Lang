import networkx as nx
import argparse
import random
import numpy as np
import torch
import torch.multiprocessing as mp
from functools import lru_cache
import time
from tqdm import tqdm


def load_graph(input_file):
    """Load graph once and cache the result"""
    G = nx.read_edgelist(input_file, delimiter=",", data=[("weight", float)])
    print("Finish loading graph")
    return G, list(G.nodes())


def output_edges(args, index):
    start_time = time.time()
    p = 1.0 / args.p
    q = 1.0 / args.q
    # Construct Graph
    G, node_list = load_graph(args.input_file)
    
    # Initialize
    n_samples = args.n_samples
    if n_samples == -1:
        n_samples = len(node_list)
    output_array = np.zeros((n_samples, args.max_length), dtype=int)
    print(f"Process {index}: Output array shape {output_array.shape}")
    
    # Create shuffled indices more efficiently
    indices = np.random.permutation(n_samples)
    
    # Use tqdm for progress tracking
    pbar = tqdm(total=n_samples, desc=f"Process {index}", position=index)
    
    for n in range(0, n_samples):
        last_node = 0
        # if selecting all nodes, start from a random node
        if n_samples == len(node_list):
            current_node = node_list[indices[n]]
        else:
            current_node = random.choice(node_list)
        output_array[n, 0] = current_node
        # iterate max_length times
        for i in range(1, args.max_length):
            neighbors = list(G.neighbors(current_node))
            if not neighbors:
                break
                
            neighbors_weight = []
            for nbr in neighbors:
                weight = G.edges[(current_node, nbr)]['weight']
                if nbr == last_node:  # d = 0
                    neighbors_weight.append(p * weight)
                elif G.has_edge(last_node, nbr):  # d = 1
                    neighbors_weight.append(weight)
                else:
                    neighbors_weight.append(q * weight)  # d = 2
                    
            last_node = current_node
            
            # Handle the case where all weights are zero
            if sum(neighbors_weight) <= 0:
                # If all weights are zero, use equal weights instead
                current_node = random.choice(neighbors)
                print(f"Process {index}: Warning - Zero weights encountered at sample {n}, path position {i}. Using random selection.")
            else:
                current_node = random.choices(neighbors, weights=neighbors_weight, k=1)[0]
                
            output_array[n, i] = current_node
        
        # Update progress bar
        pbar.update(1)
        
        # Print percentage every 5%
        if n % max(1, n_samples // 20) == 0:
            percentage = (n / n_samples) * 100
            if percentage > 0:  # Skip the 0% print
                print(f"Process {index}: {percentage:.1f}% complete")
    
    # Close progress bar
    pbar.close()
    
    # Save output
    with open(args.output_directory + str(index) + args.output_name, 'wb') as f:
        np.save(f, output_array)
    
    # Print execution time
    execution_time = time.time() - start_time
    print(f"Process {index}: Completed in {execution_time:.2f} seconds")


def output_polar_edges(args, index):
    start_time = time.time()
    p = 1.0 / args.p
    q = 1.0 / args.q
    # Construct Graph
    G, node_list = load_graph(args.input_file)
    
    # Initialize
    n_samples = args.n_samples
    if n_samples == -1:
        n_samples = len(node_list)
    output_array = np.zeros((2 * n_samples, args.max_length), dtype=int)
    print(f"Process {index}: Output array shape {output_array.shape}")
    
    # Create shuffled indices more efficiently
    indices = np.random.permutation(n_samples)
    
    # Use tqdm for progress tracking
    pbar = tqdm(total=n_samples, desc=f"Process {index}", position=index)
    
    for n in range(0, n_samples):
        last_node = 0
        if n_samples == len(node_list):
            current_node = node_list[indices[n]]
        else:
            current_node = random.choice(node_list)
        output_array[n, 0] = current_node
        current_node_positive = 1
        positive_count = 1
        negative_count = 0

        for i in range(1, args.max_length):
            neighbors = list(G.neighbors(current_node))
            if not neighbors:
                break
                
            neighbors_weight = []
            for nbr in neighbors:
                weight = G.edges[(current_node, nbr)]['weight']
                if nbr == last_node:  # d = 0
                    neighbors_weight.append(p * weight)
                elif G.has_edge(last_node, nbr):  # d = 1
                    neighbors_weight.append(weight)
                else:
                    neighbors_weight.append(q * weight)  # d = 2
                    
            last_node = current_node
            indices_weights = np.arange(len(neighbors_weight))
            
            # Handle the case where all weights are zero
            abs_weights = np.abs(neighbors_weight)
            if np.sum(abs_weights) <= 0:
                # If all weights are zero, use equal weights instead
                current_idx = random.randint(0, len(neighbors_weight) - 1)
                print(f"Process {index}: Warning - Zero weights encountered at sample {n}, path position {i}. Using random selection.")
            else:
                current_idx = random.choices(indices_weights, weights=abs_weights, k=1)[0]
            
            # neighbor is an antonym of current node
            if neighbors_weight[current_idx] < 0:
                current_node_positive *= -1
                
            # add nodes
            current_node = neighbors[current_idx]
            if current_node_positive > 0:
                # add the node to the current line
                output_array[n, positive_count] = current_node
                positive_count += 1
            else:
                # add the node to the opposite of the current line
                output_array[n_samples + n, negative_count] = current_node
                negative_count += 1
        
        # Update progress bar
        pbar.update(1)
        
        # Print percentage every 5%
        if n % max(1, n_samples // 20) == 0:
            percentage = (n / n_samples) * 100
            if percentage > 0:  # Skip the 0% print
                print(f"Process {index}: {percentage:.1f}% complete")
    
    # Close progress bar
    pbar.close()
    
    # Save output
    with open(args.output_directory + str(index) + args.output_name, 'wb') as f:
        np.save(f, output_array)
    
    # Print execution time
    execution_time = time.time() - start_time
    print(f"Process {index}: Completed in {execution_time:.2f} seconds")


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    # Path
    argparser.add_argument('--input_file', type=str, default="./temp/edge_str_weak.csv",
                           help="The path of input edge weights")
    argparser.add_argument('--max_length', type=int, default=20,
                           help="The max length of path")
    argparser.add_argument('--n_samples', type=int, default=-1,
                           help="The max length of path")
    argparser.add_argument('--p', type=float, default=1.5,
                           help="The hyperparameter p")
    argparser.add_argument('--q', type=float, default=5.0,
                           help="The hyperparameter q")
    argparser.add_argument('--output_directory', type=str, default="./path/",
                           help="The path of output numerical corpus")
    argparser.add_argument('--output_name', type=str, default="_edge_str_weak.npy",
                           help="The path of output numerical corpus")
    argparser.add_argument('--num_processes', type=int, default=5,
                           help="Number of parallel processes to run")
    argparser.add_argument('--run_mode', type=str, default="normal",
                           help="Run mode: 'normal' for str_weak edges, 'polar' for syn_ant edges")
    args = argparser.parse_args()

    print(f"Starting edge generation with input file: {args.input_file}")
    total_start_time = time.time()
    num_processes = args.num_processes
    
    # Choose processing function based on run mode
    if args.run_mode == "polar":
        target_function = output_polar_edges
        print("Running in polar mode for syn_ant edges")
    else:
        target_function = output_edges
        print("Running in normal mode for str_weak edges")
    
    # Start processing
    processes = []
    for local_rank in range(num_processes):
        p = mp.Process(target=target_function, args=(args, local_rank,))
        p.start()
        processes.append(p)
    for p in processes:
        p.join()
    
    # Print execution stats
    total_time = time.time() - total_start_time  
    print(f"Task completed in {total_time:.2f} seconds")
