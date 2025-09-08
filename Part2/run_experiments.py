#!/usr/bin/env python3
"""
Full experimental suite for concurrent file download analysis
Runs experiments with varying numbers of clients and generates data for plotting
Compatible with user's config.json format
"""

import subprocess
import sys
import time
import json
import csv
from pathlib import Path
import argparse

class ExperimentRunner:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.results_file = Path('results.csv')

    def load_config(self):
        """Load experiment configuration"""
        try:
            with Path(self.config_file).open() as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get_client_counts(self):
        """Get list of client counts to test"""
        # Use a reasonable range based on the base num_clients in config
        base_clients = self.config.get('num_clients', 5)

        # Create a sensible test range: 1, 2, then every 2 up to 4x the base
        max_clients = max(10, base_clients * 4)  # At least 20, or 4x base clients

        # Test pattern: 1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20...
        counts = [1, 2] + list(range(4, max_clients + 1, 2))

        # Limit to reasonable maximum for testing
        counts = [c for c in counts if c <= 24]  # Cap at 24 clients

        return counts

    def run_single_experiment(self, num_clients, repetition):
        """Run a single experiment using runner.py"""
        print(f"  Experiment {repetition}: {num_clients} clients...")

        try:
            # Call runner.py with the correct arguments
            cmd = [
                sys.executable, 'runner.py',
                '--clients', str(num_clients),
                '--quiet'
            ]

            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)  # Increased timeout
            end_time = time.time()

            if result.returncode == 0:
                # Parse results - runner.py outputs: SUCCESS:successful/total:avg_time
                output = result.stdout.strip()
                if 'SUCCESS:' in output:
                    try:
                        success_line = [line for line in output.splitlines() if line.startswith("SUCCESS:")][0]
                        # Format: SUCCESS:successful/total:avg_time
                        parts = success_line.split(":")
                        if len(parts) >= 3:
                            success_ratio = parts[1]  # e.g., "5/5"
                            avg_time = float(parts[2])

                            successful, total = map(int, success_ratio.split('/'))

                            print(f"    ✅ {successful}/{total} clients, avg: {avg_time:.3f} ms")
                            return {
                                'num_clients': num_clients,
                                'repetition': repetition,
                                'successful_clients': successful,
                                'total_clients': total,
                                'avg_completion_time': avg_time,
                                'experiment_duration': (end_time - start_time) * 1000
                            }
                        else:
                            print(f"    ❌ Invalid SUCCESS format: {output}")
                            return None
                    except (ValueError, IndexError) as e:
                        print(f"    ❌ Failed to parse SUCCESS output: {e}")
                        return None
                else:
                    print(f"    ❌ Unexpected output: {output}")
                    # Show more details for debugging
                    if result.stderr.strip():
                        print(f"       Error: {result.stderr.strip()}")
                    return None
            else:
                print(f"    ❌ Failed (exit code {result.returncode})")
                if result.stderr.strip():
                    error_lines = result.stderr.strip().split('\n')
                    print(f"       Error: {error_lines[-1]}")  # Show last line of error
                if result.stdout.strip():
                    print(f"       Output: {result.stdout.strip()[:100]}")  # Show first 100 chars
                return None

        except subprocess.TimeoutExpired:
            print(f"    ❌ Timed out (3 minutes)")
            return None
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None

    def save_result(self, result):
        """Save experiment result to CSV"""
        if not result:
            return

        # Create CSV file with headers if it doesn't exist
        if not self.results_file.exists():
            with self.results_file.open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'num_clients', 'repetition', 'successful_clients', 
                    'total_clients', 'avg_completion_time', 'experiment_duration'
                ])

        # Append result
        with self.results_file.open('a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result['num_clients'],
                result['repetition'], 
                result['successful_clients'],
                result['total_clients'],
                result['avg_completion_time'],
                result['experiment_duration']
            ])

    def run_full_suite(self):
        """Run the complete experimental suite"""
        client_counts = self.get_client_counts()
        num_repetitions = self.config.get('num_repetitions', 5)

        print(f"=== CONCURRENT FILE DOWNLOAD EXPERIMENTS ===")
        print(f"Config file: {self.config_file}")
        print(f"Server: {self.config.get('server_ip', '10.0.0.100')}:{self.config.get('server_port', 5000)}")
        print(f"Chunk size (k): {self.config.get('k', 5)}")
        print(f"Words file: {self.config.get('filename', 'words.txt')}")
        print(f"Client counts: {client_counts}")
        print(f"Repetitions per count: {num_repetitions}")
        print(f"Total experiments: {len(client_counts) * num_repetitions}")
        print(f"Mode: Mininet (requires sudo)")
        print(f"Results file: {self.results_file}")
        print()

        # Check if we're running with sudo
        if not self.check_sudo():
            print("❌ This experiment requires sudo privileges for Mininet")
            print("Please run: sudo python3 run_experiments.py")
            return False

        total_experiments = len(client_counts) * num_repetitions
        completed_experiments = 0
        successful_experiments = 0

        start_time = time.time()

        for num_clients in client_counts:
            print(f"Testing with {num_clients} clients:")

            for rep in range(1, num_repetitions + 1):
                completed_experiments += 1

                result = self.run_single_experiment(num_clients, rep)

                if result:
                    self.save_result(result)
                    successful_experiments += 1

                # Progress update
                progress = (completed_experiments / total_experiments) * 100
                print(f"    Progress: {completed_experiments}/{total_experiments} ({progress:.1f}%)")

                # Brief pause between experiments to let system settle
                time.sleep(2)  # Increased pause

            print()

        end_time = time.time()
        duration = end_time - start_time

        print(f"=== EXPERIMENTAL SUITE COMPLETED ===")
        print(f"Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"Successful experiments: {successful_experiments}/{total_experiments}")
        print(f"Success rate: {successful_experiments/total_experiments*100:.1f}%")
        print(f"Results saved to: {self.results_file}")

        if successful_experiments > 0:
            print("\nNext steps:")
            print("  python3 plot_results.py  # Generate plots")
            return True
        else:
            print("\n❌ No successful experiments")
            print("\nTroubleshooting:")
            print("  1. Check: bash debug_experiments.sh")
            print("  2. Test single: sudo python3 runner.py --clients 1")
            print("  3. Verify files: ls -la server.py client.py words.txt")
            return False

    def check_sudo(self):
        """Check if running with sudo privileges"""
        import os
        return os.geteuid() == 0

    def analyze_existing_results(self):
        """Analyze existing results file"""
        if not self.results_file.exists():
            print(f"No results file found: {self.results_file}")
            return

        print(f"=== ANALYZING RESULTS FROM {self.results_file} ===")

        # Read and group results
        results_by_clients = {}
        total_experiments = 0
        successful_experiments = 0

        with self.results_file.open('r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_experiments += 1
                num_clients = int(row['num_clients'])
                avg_time = float(row['avg_completion_time'])
                success_rate = int(row['successful_clients']) / int(row['total_clients'])

                if num_clients not in results_by_clients:
                    results_by_clients[num_clients] = {'times': [], 'success_rates': []}

                # Only include successful experiments (positive completion time)
                if avg_time > 0:
                    results_by_clients[num_clients]['times'].append(avg_time)
                    results_by_clients[num_clients]['success_rates'].append(success_rate)
                    successful_experiments += 1

        print(f"\nOverall Results:")
        print(f"Total experiments: {total_experiments}")
        print(f"Successful experiments: {successful_experiments}")
        print(f"Success rate: {successful_experiments/total_experiments*100:.1f}%")

        # Calculate statistics
        print("\nResults by Client Count:")
        print("Clients | Avg Time (ms) | Std Dev | Success Rate | Samples")
        print("--------|---------------|---------|--------------|--------")

        for num_clients in sorted(results_by_clients.keys()):
            data = results_by_clients[num_clients]
            times = data['times']
            success_rates = data['success_rates']

            if times:
                avg_time = sum(times) / len(times)
                if len(times) > 1:
                    variance = sum((t - avg_time) ** 2 for t in times) / (len(times) - 1)
                    std_dev = variance ** 0.5
                else:
                    std_dev = 0.0

                avg_success = sum(success_rates) / len(success_rates)

                print(f"{num_clients:7d} | {avg_time:11.1f} | {std_dev:7.1f} | {avg_success:10.1%} | {len(times):6d}")

        # Performance scaling analysis
        if len(results_by_clients) >= 2:
            client_counts = sorted(results_by_clients.keys())

            # Get baseline (single client or minimum)
            baseline_data = results_by_clients[client_counts[0]]
            if baseline_data['times']:
                baseline_time = sum(baseline_data['times']) / len(baseline_data['times'])

                print(f"\nPerformance Scaling Analysis:")
                print(f"Baseline ({client_counts[0]} client{'s' if client_counts[0] > 1 else ''}): {baseline_time:.1f} ms")

                for num_clients in client_counts[1:]:
                    data = results_by_clients[num_clients]
                    if data['times']:
                        avg_time = sum(data['times']) / len(data['times'])
                        scaling_factor = avg_time / baseline_time
                        print(f"{num_clients} clients: {avg_time:.1f} ms (×{scaling_factor:.2f})")

                # Overall scaling assessment
                final_data = results_by_clients[client_counts[-1]]
                if final_data['times']:
                    final_time = sum(final_data['times']) / len(final_data['times'])
                    overall_scaling = final_time / baseline_time

                    print(f"\nOverall Scaling:")
                    print(f"{client_counts[0]} → {client_counts[-1]} clients: ×{overall_scaling:.2f} scaling factor")

                    if overall_scaling > 3.0:
                        print("✅ Strong FIFO queueing effect observed")
                    elif overall_scaling > 2.0:
                        print("✅ Moderate FIFO queueing effect observed") 
                    elif overall_scaling > 1.5:
                        print("⚠️ Some queueing effect observed")
                    else:
                        print("❌ Limited queueing effect - check server implementation")

def main():
    parser = argparse.ArgumentParser(description='Run concurrent download experiments')
    parser.add_argument('--analyze', action='store_true', 
                       help='Analyze existing results instead of running experiments')
    parser.add_argument('--config', default='config.json', help='Configuration file')

    args = parser.parse_args()

    runner = ExperimentRunner(args.config)

    if args.analyze:
        runner.analyze_existing_results()
    else:
        success = runner.run_full_suite()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
