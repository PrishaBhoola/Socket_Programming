#!/usr/bin/env python3
"""
Full experimental suite for Greedy Client FCFS Analysis (Part 3)
- FINAL STABLE VERSION
- This version runs experiments for c values from 1 to 10 to
  generate a complete and accurate graph as per the assignment.
"""

import subprocess
import sys
import time
import json
import csv
from pathlib import Path
import argparse
import os

class GreedyExperimentRunner:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.results_file = Path('fairness_results.csv')

    def load_config(self):
        """Load experiment configuration"""
        try:
            with Path(self.config_file).open() as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get_c_values(self):
        """Get list of c values to test (1 to 10 as per assignment)"""
        return list(range(1, 11))

    def run_single_experiment(self, num_clients, c_value, repetition):
        """Run single experiment with specified c value"""
        print(f"  Running c={c_value}, Repetition #{repetition}...")

        try:
            # Use sudo if not already running as root
            sudo_prefix = [] if os.geteuid() == 0 else ['sudo']
            cmd = sudo_prefix + [
                sys.executable, 'runner.py',
                '--clients', str(num_clients),
                '--c', str(c_value),
                '--quiet'
            ]

            # Set a generous timeout for the entire run
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                output = result.stdout.strip()
                success_line = next((line for line in output.splitlines() if line.startswith("SUCCESS:")), None)
                
                if success_line:
                    parts = success_line.split(':')
                    # SUCCESS:total_clients:greedy_time:normal_avg:fairness_ratio:jains_index
                    if len(parts) == 6:
                        greedy_time = float(parts[2])
                        normal_avg_time = float(parts[3])
                        fairness_ratio = float(parts[4])
                        jains_index = float(parts[5])

                        print(f"    ✅ Success: ratio={fairness_ratio:.2f}x, JFI={jains_index:.3f}")

                        return {
                            'num_clients': num_clients,
                            'c_value': c_value,
                            'repetition': repetition,
                            'greedy_completion_time': greedy_time,
                            'normal_avg_completion_time': normal_avg_time,
                            'fairness_ratio': fairness_ratio,
                            'jains_index': jains_index,
                        }
                print(f"    ❌ FAILED (Could not parse SUCCESS line from output):\n--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}")
                return None
            else:
                print(f"    ❌ FAILED (runner.py exited with code {result.returncode}):\n--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("    ❌ FAILED (Timed out after 300s)")
            return None
        except Exception as e:
            print(f"    ❌ FAILED (Error: {e})")
            return None

    def save_result(self, result):
        """Save experiment result to CSV."""
        if not result:
            return

        # Create CSV with headers if it doesn't exist
        if not self.results_file.exists():
            with self.results_file.open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'num_clients', 'c_value', 'repetition',
                    'greedy_completion_time', 'normal_avg_completion_time',
                    'fairness_ratio', 'jains_index'
                ])

        with self.results_file.open('a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result['num_clients'],
                result['c_value'],
                result['repetition'],
                result['greedy_completion_time'],
                result['normal_avg_completion_time'],
                result['fairness_ratio'],
                result['jains_index']
            ])

    def run_full_suite(self):
        """Run complete experimental suite"""
        c_values = self.get_c_values()
        num_clients = self.config.get('num_clients', 10)
        num_repetitions = 1 # Run 3 times for better averaging

        # Clear previous results
        if self.results_file.exists():
            self.results_file.unlink()

        print("=== STARTING FCFS FAIRNESS EXPERIMENTAL SUITE ===")
        print(f"Number of clients: {num_clients}")
        print(f"Values for 'c': {c_values}")
        print(f"Repetitions per 'c': {num_repetitions}")
        print("===============================================\n")

        total_experiments = len(c_values) * num_repetitions
        successful = 0

        for i, c_value in enumerate(c_values):
            print(f"--- Testing with c = {c_value} ---")
            print(f"Progress: ({i+1}/{len(c_values)})")
            
            for rep in range(1, num_repetitions + 1):
                result = self.run_single_experiment(num_clients, c_value, rep)
                if result:
                    self.save_result(result)
                    successful += 1
                time.sleep(1) # Brief pause between runs
            print("-" * 20)

        print("\n=== EXPERIMENTAL SUITE COMPLETE ===")
        print(f"Successful runs: {successful}/{total_experiments}")
        print(f"Final results are in '{self.results_file}'")
        print("\nTo visualize the results, run: python3 plot.py")
        return successful > 0

def main():
    parser = argparse.ArgumentParser(description='Greedy client fairness experiments')
    args = parser.parse_args()

    runner = GreedyExperimentRunner()
    success = runner.run_full_suite()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

