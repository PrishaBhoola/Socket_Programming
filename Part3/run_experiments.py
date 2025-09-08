#!/usr/bin/env python3
"""
Full experimental suite for Greedy Client FCFS Analysis (Part 3)
Varies the number of greedy requests (c) to analyze fairness impact
"""

import subprocess
import sys
import time
import json
import csv
from pathlib import Path
import argparse

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
        """Get list of c values to test"""
        base_c = self.config.get('c', 10)

        # Test range: 1, 2, 5, 10, 15, 20, 25, 30
        c_values = [1, 2, 5] 
        # + list(range(10, min(31, base_c * 3 + 1), 5))
        return sorted(set(c_values))  # Remove duplicates and sort

    def run_single_experiment(self, num_clients, c_value, repetition):
        """Run single experiment with specified c value"""
        print(f"  Experiment {repetition}: c={c_value}")

        try:
            cmd = [
                sys.executable, 'runner.py',
                '--clients', str(num_clients),
                '--c', str(c_value),
                '--quiet'
            ]

            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            end_time = time.time()

            if result.returncode == 0:
                output = result.stdout.strip()
                if "SUCCESS:" in output:
                    success_line = [line for line in output.splitlines() if line.startswith("SUCCESS:")][0]
                    # Parse: SUCCESS:total_clients:greedy_time:normal_avg:fairness_ratio
                    parts = success_line.split(':')
                    if len(parts) >= 5:
                        total_clients = int(parts[1])
                        greedy_time = float(parts[2])
                        normal_avg_time = float(parts[3])
                        fairness_ratio = float(parts[4])

                        print(f"    ✅ c={c_value}: greedy={greedy_time:.1f}ms, normal_avg={normal_avg_time:.1f}ms, ratio={fairness_ratio:.2f}x")

                        return {
                            'num_clients': num_clients,
                            'c_value': c_value,
                            'repetition': repetition,
                            'greedy_completion_time': greedy_time,
                            'normal_avg_completion_time': normal_avg_time,
                            'fairness_ratio': fairness_ratio,
                            'experiment_duration': (end_time - start_time) * 1000
                        }
                    else:
                        print(f"    ❌ Invalid SUCCESS format: {output}")
                        return None
                else:
                    print(f"    ❌ Unexpected output: {output}")
                    return None
            else:
                print(f"    ❌ Failed (exit code {result.returncode})")
                if result.stderr.strip():
                    print(f"       Error: {result.stderr.strip()}")
                return None

        except subprocess.TimeoutExpired:
            print(f"    ❌ Timed out")
            return None
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None

    def save_result(self, result):
        """Save experiment result to CSV"""
        if not result:
            return

        # Create CSV with headers if it doesn't exist
        if not self.results_file.exists():
            with self.results_file.open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'num_clients', 'c_value', 'repetition',
                    'greedy_completion_time', 'normal_avg_completion_time',
                    'fairness_ratio', 'experiment_duration'
                ])

        # Append result
        with self.results_file.open('a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result['num_clients'],
                result['c_value'],
                result['repetition'],
                result['greedy_completion_time'],
                result['normal_avg_completion_time'],
                result['fairness_ratio'],
                result['experiment_duration']
            ])

    def run_full_suite(self):
        """Run complete experimental suite"""
        c_values = self.get_c_values()
        num_clients = self.config.get('num_clients', 10)
        num_repetitions = 3  # Fixed for fairness analysis

        print(f"=== GREEDY CLIENT FAIRNESS EXPERIMENTS ===")
        print(f"Total clients: {num_clients} (1 greedy, {num_clients-1} normal)")
        print(f"C values (greedy requests): {c_values}")
        print(f"Repetitions per c value: {num_repetitions}")
        print(f"Total experiments: {len(c_values) * num_repetitions}")
        print(f"Results file: {self.results_file}")
        print()

        # Check sudo
        if not self.check_sudo():
            print("❌ Requires sudo for Mininet")
            print("Run: sudo python3 run_experiments.py")
            return False

        total_experiments = len(c_values) * num_repetitions
        completed = 0
        successful = 0

        start_time = time.time()

        for c_value in c_values:
            print(f"Testing with c={c_value} (greedy client sends {c_value} requests):")

            for rep in range(1, num_repetitions + 1):
                completed += 1

                result = self.run_single_experiment(num_clients, c_value, rep)

                if result:
                    self.save_result(result)
                    successful += 1

                progress = (completed / total_experiments) * 100
                print(f"    Progress: {completed}/{total_experiments} ({progress:.1f}%)")

                time.sleep(1)  # Brief pause

            print()

        end_time = time.time()
        duration = end_time - start_time

        print(f"=== EXPERIMENTAL SUITE COMPLETED ===")
        print(f"Total time: {duration:.1f} seconds")
        print(f"Successful experiments: {successful}/{total_experiments}")
        print(f"Success rate: {successful/total_experiments*100:.1f}%")
        print(f"Results saved to: {self.results_file}")

        if successful > 0:
            print("\nNext steps:")
            print("  python3 plot.py        # Generate fairness plots")
            print("  make plot              # Alternative plot command")
            return True
        else:
            print("\n❌ No successful experiments")
            return False

    def check_sudo(self):
        """Check if running with sudo"""
        import os
        return os.geteuid() == 0

    def analyze_existing_results(self):
        """Analyze existing results"""
        if not self.results_file.exists():
            print(f"No results file: {self.results_file}")
            return

        print(f"=== FAIRNESS ANALYSIS FROM {self.results_file} ===")

        # Read results
        results_by_c = {}

        with self.results_file.open('r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                c_value = int(row['c_value'])
                fairness_ratio = float(row['fairness_ratio'])
                greedy_time = float(row['greedy_completion_time'])
                normal_time = float(row['normal_avg_completion_time'])

                if c_value not in results_by_c:
                    results_by_c[c_value] = {
                        'fairness_ratios': [],
                        'greedy_times': [],
                        'normal_times': []
                    }

                results_by_c[c_value]['fairness_ratios'].append(fairness_ratio)
                results_by_c[c_value]['greedy_times'].append(greedy_time)
                results_by_c[c_value]['normal_times'].append(normal_time)

        # Analysis
        print("\nFairness Analysis by C Value:")
        print("C Value | Avg Fairness Ratio | Greedy Time | Normal Time | Samples")
        print("--------|--------------------|-----------  |-------------|--------")

        for c_value in sorted(results_by_c.keys()):
            data = results_by_c[c_value]

            avg_fairness = sum(data['fairness_ratios']) / len(data['fairness_ratios'])
            avg_greedy = sum(data['greedy_times']) / len(data['greedy_times'])
            avg_normal = sum(data['normal_times']) / len(data['normal_times'])
            samples = len(data['fairness_ratios'])

            print(f"{c_value:7d} | {avg_fairness:18.2f} | {avg_greedy:9.1f} ms | {avg_normal:9.1f} ms | {samples:6d}")

        # Fairness insights
        print("\n=== FAIRNESS INSIGHTS ===")

        if len(results_by_c) >= 2:
            c_values = sorted(results_by_c.keys())

            print(f"As c increases from {c_values[0]} to {c_values[-1]}:")

            first_fairness = sum(results_by_c[c_values[0]]['fairness_ratios']) / len(results_by_c[c_values[0]]['fairness_ratios'])
            last_fairness = sum(results_by_c[c_values[-1]]['fairness_ratios']) / len(results_by_c[c_values[-1]]['fairness_ratios'])

            print(f"  Fairness ratio: {first_fairness:.2f} → {last_fairness:.2f}")

            if last_fairness > first_fairness * 1.5:
                print("  ✅ Strong unfairness effect observed")
            elif last_fairness > first_fairness * 1.2:
                print("  ⚠️ Moderate unfairness effect")
            else:
                print("  ❓ Limited unfairness effect")

            # Expected vs actual
            expected_ratio_change = c_values[-1] / c_values[0]
            actual_ratio_change = last_fairness / first_fairness

            print(f"  Expected ratio change: {expected_ratio_change:.2f}x")
            print(f"  Actual ratio change: {actual_ratio_change:.2f}x")
            print(f"  Efficiency: {actual_ratio_change/expected_ratio_change:.2f}")

def main():
    parser = argparse.ArgumentParser(description='Greedy client fairness experiments')
    parser.add_argument('--analyze', action='store_true', help='Analyze existing results')
    parser.add_argument('--config', default='config.json', help='Config file')

    args = parser.parse_args()

    runner = GreedyExperimentRunner(args.config)

    if args.analyze:
        runner.analyze_existing_results()
    else:
        success = runner.run_full_suite()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
