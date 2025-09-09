#!/usr/bin/env python3
"""
Full Experimental Suite for Greedy Client FCFS Analysis (Part 3)
- Runs the FCFS experiment for a range of 'c' values.
- Repeats each experiment multiple times to ensure reliable results.
- Saves all results to a CSV file for plotting and analysis.
"""

import subprocess
import sys
import time
import json
import csv
from pathlib import Path
import argparse
import os

def load_config(config_file='config.json'):
    """Loads the base configuration for the experiments."""
    try:
        with Path(config_file).open() as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load configuration. {e}")
        return {}

def run_single_iteration(num_clients, c_value, repetition):
    """
    Executes one iteration of the experiment by calling the runner.py script.
    """
    print(f"  Running c={c_value}, Repetition #{repetition}...")
    cmd = [
        'sudo', sys.executable, 'runner.py',
        '--clients', str(num_clients),
        '--c', str(c_value),
        '--quiet'
    ]
    
    try:
        # We need a long timeout as Mininet setup and the experiment can be slow.
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=360)

        if result.returncode == 0 and result.stdout.strip().startswith("SUCCESS"):
            # Parse the machine-readable output from runner.py
            # Format: SUCCESS:total_clients:greedy_time:normal_avg:advantage_ratio:jains_index
            parts = result.stdout.strip().split(':')
            return {
                'num_clients': int(parts[1]),
                'c_value': c_value,
                'repetition': repetition,
                'greedy_completion_time': float(parts[2]),
                'normal_avg_completion_time': float(parts[3]),
                'advantage_ratio': float(parts[4]),
                'jains_fairness_index': float(parts[5]),
                'status': 'success'
            }
        else:
            print(f"    -> FAILED. Return code: {result.returncode}")
            print(f"    -> STDOUT: {result.stdout.strip()}")
            print(f"    -> STDERR: {result.stderr.strip()}")
            return {'c_value': c_value, 'status': 'failed'}

    except subprocess.TimeoutExpired:
        print("    -> FAILED: Timeout expired. The experiment took too long.")
        return {'c_value': c_value, 'status': 'timeout'}
    except Exception as e:
        print(f"    -> FAILED: An unexpected error occurred: {e}")
        return {'c_value': c_value, 'status': 'error'}

def save_results(results, filename='fairness_results.csv'):
    """Saves the collected results into a CSV file."""
    if not results:
        return
        
    # Check if the file exists to decide whether to write headers
    file_exists = Path(filename).is_file()
    
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        if not file_exists:
            writer.writeheader()
        for result in results:
            if result['status'] == 'success':
                writer.writerow(result)
    print(f"\nResults appended to '{filename}'")

def run_experimental_suite():
    """
    Main function to run the entire suite of experiments.
    """
    config = load_config()
    num_clients = config.get('num_clients', 10)
    
    # Define the range of 'c' values and number of repetitions
    c_values_to_test = [1, 4, 8, 12, 16, 20, 24, 28, 32]
    repetitions_per_c = 1

    print("=== STARTING FCFS FAIRNESS EXPERIMENTAL SUITE ===")
    print(f"Number of clients: {num_clients}")
    print(f"Values for 'c': {c_values_to_test}")
    print(f"Repetitions per 'c': {repetitions_per_c}")
    print("===============================================")
    
    # Clean up old results file
    results_file = 'fairness_results.csv'
    if Path(results_file).exists():
        os.remove(results_file)
        print(f"Removed old results file: '{results_file}'")

    all_results = []
    total_runs = len(c_values_to_test) * repetitions_per_c
    completed_runs = 0

    for c in c_values_to_test:
        print(f"\n--- Testing with c = {c} ---")
        for rep in range(1, repetitions_per_c + 1):
            completed_runs += 1
            print(f"Progress: ({completed_runs}/{total_runs})")
            
            result = run_single_iteration(num_clients, c, rep)
            all_results.append(result)
            
            # Save results incrementally
            if result['status'] == 'success':
                 save_results([result], results_file)

    successful_runs = sum(1 for r in all_results if r['status'] == 'success')
    
    print("\n=== EXPERIMENTAL SUITE COMPLETE ===")
    print(f"Total runs: {total_runs}")
    print(f"Successful runs: {successful_runs}")
    print(f"Failed/Timeout runs: {total_runs - successful_runs}")
    print(f"Final results are in '{results_file}'")
    print("\nTo visualize the results, run: python3 plot.py")


def main():
    if os.geteuid() != 0:
        print("This script calls a Mininet script and must be run with sudo.")
        print("--> sudo python3 run_experiments.py")
        sys.exit(1)
    run_experimental_suite()

if __name__ == "__main__":
    main()
