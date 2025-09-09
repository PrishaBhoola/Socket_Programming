#!/usr/bin/env python3
"""
FCFS Turn-Based Experiment Runner (Part 3)
- FINAL STABLE VERSION
- This version uses a lightweight, stable polling mechanism to monitor clients,
  fixing both the 'Killed' (OOM) errors and allowing the experiment to run
  to completion for all 'c' values to generate an accurate graph.
"""

import sys
import time
import json
import os
from pathlib import Path
import argparse
import numpy as np

# Import Mininet libraries
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel
from topology import GreedyClientTopo

# --- Constants ---
CLIENT_COMPLETION_TIMEOUT = 240  # Increased timeout for high 'c' values

def load_config(config_file='config.json'):
    try:
        with Path(config_file).open() as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load config file: {e}", file=sys.stderr)
        return {}

def analyze_results(results: list):
    """Calculates fairness metrics from a list of client results."""
    if not results:
        return None

    greedy_times = [r['time'] for r in results if r['type'] == 'GREEDY']
    normal_times = [r['time'] for r in results if r['type'] == 'NORMAL']

    if not greedy_times or not normal_times:
        return None

    greedy_avg_time = np.mean(greedy_times)
    normal_avg_time = np.mean(normal_times)
    
    all_times = [1/r['time'] for r in results]
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
        
        server = net.get('server')
        server.cmd('python3 server.py > server.log 2>&1 &')
        if verbose:
            print("Server process started. Waiting for it to initialize...")
        time.sleep(2) 

        if verbose:
            print(f"Starting {num_clients} clients ({greedy_client_id} is greedy with c={c_value})...")
        
        for i in range(1, num_clients + 1):
            client_name = f'client{i}'
            client = net.get(client_name)
            log_file_path = f"/tmp/{client_name}.log" # Use /tmp for logs
            
            cmd_args = ['python3', 'client.py', '--client-id', client_name, '--quiet']
            if client_name == greedy_client_id:
                cmd_args.extend(['--greedy', '--c', str(c_value)])
            
            cmd = ' '.join(cmd_args) + f' > {log_file_path} 2>&1 &'
            client.cmd(cmd)

        if verbose:
            print("Waiting for all clients to complete...")
        
        start_time = time.time()
        all_done = False
        while time.time() - start_time < CLIENT_COMPLETION_TIMEOUT:
            still_running = 0
            for i in range(1, num_clients + 1):
                client = net.get(f'client{i}')
                # Use pgrep for a lightweight process check
                pattern = f"client.py --client-id client{i}"
                result = client.cmd(f'pgrep -f "{pattern}"')
                if result.strip():
                    still_running += 1
            
            if still_running == 0:
                all_done = True
                if verbose:
                    print("✅ All clients have completed.")
                break
            
            time.sleep(2)

        if not all_done:
            print(f"*** TIMEOUT: Not all clients finished within {CLIENT_COMPLETION_TIMEOUT}s.", file=sys.stderr)

        if verbose:
            print("Collecting results...")
        
        results = []
        for i in range(1, num_clients + 1):
            client_name = f'client{i}'
            log_file_path = f"/tmp/{client_name}.log"
            client_host = net.get(client_name)
            output = client_host.cmd(f'cat {log_file_path}').strip()
            
            try:
                parts = output.split(':')
                if len(parts) == 4 and parts[0] == "ELAPSED_MS":
                    results.append({'client': client_name, 'time': float(parts[1]), 'type': parts[3]})
            except (ValueError, IndexError):
                if verbose:
                    print(f"  - Could not parse result for {client_name}", file=sys.stderr)
        
        return results

    except Exception as e:
        print(f"FATAL ERROR during experiment: {e}", file=sys.stderr)
        return []
    finally:
        if net:
            for host in net.hosts:
                host.cmd('pkill -9 -f "client.py"')
                host.cmd('pkill -9 -f "server.py"')
            if verbose:
                print("--- Stopping Mininet ---")
            net.stop()

def main():
    parser = argparse.ArgumentParser(description="Greedy Client FCFS Fairness Experiment Runner")
    parser.add_argument('--clients', type=int, help="Number of clients to run in the experiment")
    parser.add_argument('--c', type=int, help="Number of requests per turn for the greedy client")
    parser.add_argument('--greedy-id', type=str, default='client1', help="Which client should be greedy")
    parser.add_argument('--quiet', action='store_true', help="Run Mininet with less verbose output")
    args = parser.parse_args()

    config = load_config()
    num_clients = args.clients or config.get('num_clients', 10)
    c_value = args.c or config.get('c', 10)

    results = run_mininet_experiment(num_clients, c_value, args.greedy_id, not args.quiet)

    if results and len(results) == num_clients:
        analysis = analyze_results(results)
        if analysis:
            if not args.quiet:
                print("\n--- ANALYSIS SUMMARY ---")
                print(f"Greedy Client Time (c={c_value}): {analysis['greedy_completion_time']:.2f} ms")
                print(f"Average Normal Client Time: {analysis['normal_avg_time']:.2f} ms")
                print(f"Greedy Advantage: {analysis['fairness_ratio']:.2f}x faster")
                print(f"Jain's Fairness Index: {analysis['jains_index']:.4f} (1.0 is perfect fairness)")

            print(f"SUCCESS:{analysis['total_clients']}:{analysis['greedy_completion_time']:.3f}:{analysis['normal_avg_time']:.3f}:{analysis['fairness_ratio']:.3f}:{analysis['jains_index']:.4f}")
            sys.exit(0)

    if not args.quiet:
        failed_count = num_clients - len(results)
        print(f"\n=== Experiment FAILED: {failed_count} client(s) did not report results ===", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()

