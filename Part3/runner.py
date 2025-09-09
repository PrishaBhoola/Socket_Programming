#!/usr/bin/env python3
"""
FCFS Turn-Based Experiment Runner (Part 3)
- FINAL CORRECTED VERSION
- This runner correctly launches the greedy client with the required '--c'
  argument and robustly waits for all clients to finish before analysis.
- Suppresses summary output in --quiet mode to ensure clean parsing by other scripts.
- ADDED MASTER TIMEOUT to prevent hung processes from stalling the entire suite.
"""

import subprocess
import sys
import time
import json
import os
from pathlib import Path
import argparse
import numpy as np

# (Assuming topology.py with GreedyClientTopo is in the same directory)
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel
from topology import GreedyClientTopo

# --- Constants ---
# Master timeout for waiting for all clients to complete.
CLIENT_COMPLETION_TIMEOUT = 120  # seconds

def load_config(config_file='config.json'):
    try:
        with Path(config_file).open() as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load config file: {e}", file=sys.stderr)
        return {}

def create_default_config():
    config = {
        "server_ip": "10.0.0.100",
        "port": 8887,
        "num_clients": 10,
        "c": 10,
        "k": 5
    }
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("--- Created default config.json ---")

def create_words_file(num_words=100):
    if not Path('words.txt').exists():
        words = [f"word_{i:03d}" for i in range(num_words)]
        content = ','.join(words)
        with open('words.txt', 'w') as f:
            f.write(content)
        print(f"--- Created words.txt with {num_words} words ---")

def analyze_results(results: list):
    """Calculates fairness metrics but does not print them."""
    if not results:
        return None

    greedy_times = [r['time'] for r in results if r['type'] == 'GREEDY']
    normal_times = [r['time'] for r in results if r['type'] == 'NORMAL']

    if not greedy_times or not normal_times:
        # This can happen if the greedy client timed out and produced no result
        return None

    greedy_avg_time = np.mean(greedy_times)
    normal_avg_time = np.mean(normal_times)
    
    all_times = [r['time'] for r in results]
    sum_of_times = sum(all_times)
    sum_of_squares = sum(x**2 for x in all_times)
    n = len(all_times)
    jains_index = (sum_of_times**2) / (n * sum_of_squares) if sum_of_squares > 0 else 1.0
    advantage = normal_avg_time / greedy_avg_time if greedy_avg_time > 0 else float('inf')

    return {
        "total_clients": n,
        "greedy_completion_time": greedy_avg_time,
        "normal_avg_time": normal_avg_time,
        "fairness_ratio": advantage,
        "jains_index": jains_index
    }

def run_mininet_experiment(num_clients: int, c_value: int, greedy_client_id: str, verbose: bool):
    if not verbose:
        setLogLevel('error')
    else:
        setLogLevel('info')

    net = None
    try:
        topo = GreedyClientTopo(num_clients)
        net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink, cleanup=True)
        net.start()
        
        if verbose:
            print(f"*** Mininet started with {num_clients} clients. Pinging...")
            loss = net.pingAll()
            if loss > 0:
                 print(f"*** WARNING: {loss}% packet loss in network. Results may be unstable.", file=sys.stderr)

        server = net.get('server')
        server.cmd('python3 server.py > server.log 2>&1 &')
        if verbose:
            print("Server process started. Waiting for it to initialize...")
        time.sleep(2) 

        client_procs = {}
        if verbose:
            print(f"Started {num_clients} clients ({greedy_client_id} is greedy with c={c_value}). Waiting for completion...")

        for i in range(1, num_clients + 1):
            client_name = f'client{i}'
            client = net.get(client_name)
            log_file = f"{client_name}.log"
            
            cmd_args = ['python3', 'client.py', '--client-id', client_name, '--quiet']
            if client_name == greedy_client_id:
                cmd_args.extend(['--greedy', '--c', str(c_value)])
            
            cmd = ' '.join(cmd_args) + f' > {log_file} 2>&1'
            client_procs[client_name] = client.popen(cmd, shell=True)

        # --- MODIFIED: Wait for processes with a master timeout ---
        start_time = time.time()
        for client_name, proc in client_procs.items():
            remaining_time = CLIENT_COMPLETION_TIMEOUT - (time.time() - start_time)
            if remaining_time <= 0:
                print(f"*** MASTER TIMEOUT exceeded waiting for {client_name}.", file=sys.stderr)
                break
            try:
                proc.wait(timeout=remaining_time)
            except subprocess.TimeoutExpired:
                print(f"*** TIMEOUT: Client {client_name} did not complete in time.", file=sys.stderr)
        
        if verbose:
            print("All client processes have completed or timed out.")
            print("Collecting results...")

        results = []
        for i in range(1, num_clients + 1):
            client_name = f'client{i}'
            log_file = f"{client_name}.log"
            try:
                with open(log_file, 'r') as f:
                    output = f.read().strip()
                    parts = output.split(':')
                    if len(parts) == 4 and parts[0] == "ELAPSED_MS":
                        results.append({'client': client_name, 'time': float(parts[1]), 'type': parts[3]})
            except (FileNotFoundError, IndexError, ValueError):
                pass # Ignore failed or timed-out clients
            finally:
                if os.path.exists(log_file):
                    os.remove(log_file)
        
        return results

    except Exception as e:
        print(f"FATAL ERROR during experiment: {e}", file=sys.stderr)
        return []
    finally:
        # Forcefully terminate any lingering processes to ensure a clean slate
        if net:
            for host in net.hosts:
                host.cmd('pkill -9 python3')
            if verbose:
                print("--- Stopping Mininet ---")
            net.stop()

def main():
    parser = argparse.ArgumentParser(description="Greedy Client FCFS Fairness Experiment Runner")
    parser.add_argument('--setup', action='store_true', help="Create default config and words.txt files")
    parser.add_argument('--clients', type=int, help="Number of clients to run in the experiment")
    parser.add_argument('--c', type=int, help="Number of requests per turn for the greedy client")
    parser.add_argument('--greedy-id', type=str, default='client1', help="Which client should be greedy")
    parser.add_argument('--quiet', action='store_true', help="Run Mininet with less verbose output")
    args = parser.parse_args()

    if args.setup:
        create_default_config()
        create_words_file()
        return

    config = load_config()
    num_clients = args.clients or config.get('num_clients', 10)
    c_value = args.c or config.get('c', 10)

    if not Path('config.json').exists(): create_default_config()
    if not Path('words.txt').exists(): create_words_file()

    results = run_mininet_experiment(num_clients, c_value, args.greedy_id, not args.quiet)

    if results:
        analysis = analyze_results(results)
        if analysis:
            if not args.quiet:
                print("\n--- ANALYSIS SUMMARY ---")
                print(f"Greedy Client Time (c={c_value}): {analysis['greedy_completion_time']:.2f} ms")
                print(f"Average Normal Client Time: {analysis['normal_avg_time']:.2f} ms")
                print(f"Greedy Advantage: {analysis['fairness_ratio']:.2f}x faster")
                print(f"Jain's Fairness Index: {analysis['jains_index']:.4f} (1.0 is perfect fairness)")

            # Always print the machine-readable line for the calling script
            print(f"SUCCESS:{analysis['total_clients']}:{analysis['greedy_completion_time']:.3f}:{analysis['normal_avg_time']:.3f}:{analysis['fairness_ratio']:.3f}:{analysis['jains_index']:.4f}")
            sys.exit(0)

    if not args.quiet:
        print("\n=== Experiment FAILED: Not enough data for analysis ===", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()

