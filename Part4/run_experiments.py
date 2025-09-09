#!/usr/bin/env python3
"""
Full experimental suite for Round-Robin Fairness Analysis (Part 4)
- This script runs the round-robin experiment for c values from 1 to 10.
- It saves results to 'fairness_results_rr.csv'.
"""

import subprocess
import sys
import time
import json
import csv
from pathlib import Path
import os

class RoundRobinExperimentRunner:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.results_file = Path('fairness_results_rr.csv') # Separate results file

    def load_config(self):
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
        """Run single experiment using the round-robin runner."""
        print(f"  Running c={c_value}, Repetition #{repetition}...")

        try:
            sudo_prefix = [] if os.geteuid() == 0 else ['sudo']
            cmd = sudo_prefix + [
                sys.executable, 'runner.py', # Use the RR runner
                '--clients', str(num_clients),
                '--c', str(c_value),
                '--quiet'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=360)

            if result.returncode == 0:
                output = result.stdout.strip()
                success_line = next((line for line in output.splitlines() if line.startswith("SUCCESS:")), None)
                
                if success_line:
                    parts = success_line.split(':')
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
                print(f"    ❌ FAILED (Parse Error):\n{result.stdout}\n{result.stderr}")
                return None
            else:
                print(f"    ❌ FAILED (Exit Code {result.returncode}):\n{result.stdout}\n{result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("    ❌ FAILED (Timed out after 360s)")
            return None
        except Exception as e:
            print(f"    ❌ FAILED (Error: {e})")
            return None

    def save_result(self, result):
        """Save experiment result to the round-robin CSV."""
        if not result: return

        if not self.results_file.exists():
            with self.results_file.open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['num_clients', 'c_value', 'repetition', 'greedy_completion_time', 'normal_avg_completion_time', 'fairness_ratio', 'jains_index'])

        with self.results_file.open('a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result['num_clients'], result['c_value'], result['repetition'],
                result['greedy_completion_time'], result['normal_avg_completion_time'],
                result['fairness_ratio'], result['jains_index']
            ])

    def run_full_suite(self):
        """Run the complete experimental suite for round-robin."""
        c_values = self.get_c_values()
        num_clients = self.config.get('num_clients', 10)
        num_repetitions = 1

        if self.results_file.exists():
            self.results_file.unlink()

        print("=== STARTING ROUND-ROBIN FAIRNESS EXPERIMENTAL SUITE (Part 4) ===")
        print(f"Clients: {num_clients}, 'c' values: {c_values}, Repetitions: {num_repetitions}")
        print("="*60 + "\n")

        total_experiments = len(c_values) * num_repetitions
        successful = 0

        for i, c_value in enumerate(c_values):
            print(f"--- Testing with c = {c_value} (Progress: {i+1}/{len(c_values)}) ---")
            for rep in range(1, num_repetitions + 1):
                result = self.run_single_experiment(num_clients, c_value, rep)
                if result:
                    self.save_result(result)
                    successful += 1
                time.sleep(1)
            print("-" * 20)

        print("\n=== EXPERIMENTAL SUITE COMPLETE ===")
        print(f"Successful runs: {successful}/{total_experiments}")
        print(f"Final results are in '{self.results_file}'")
        print("\nTo visualize the results, run: make plot-rr")
        return successful > 0

if __name__ == "__main__":
    runner = RoundRobinExperimentRunner()
    success = runner.run_full_suite()
    sys.exit(0 if success else 1)
