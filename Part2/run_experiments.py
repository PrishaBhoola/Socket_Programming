import subprocess
import sys
import time
import csv
import json
import os

def run_experiment(num_clients, repetition):
    """Run experiment with specified number of clients."""
    start_time = time.time()

    # Launch all clients simultaneously
    processes = [
        subprocess.Popen([sys.executable, 'client.py'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        for _ in range(num_clients)
    ]

    # Wait for all clients to complete
    for proc in processes:
        proc.wait()

    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    return elapsed_ms


if __name__ == "__main__":
    # Load config
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in config.json")
        sys.exit(1)
    
    num_reps = config.get("num_repetitions", 5)

    print(f"Running experiments with {num_reps} repetitions each...")
    print("Testing concurrent clients from 1 to 32 (incremented by 4)...")

    # Create results file
    with open("results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["clients", "repetition", "completion_time"])

        # Test from 1 to 32 clients, incremented by 4
        # 1, 5, 9, 13, 17, 21, 25, 29 (following increment by 4 pattern)
        client_counts = [1] + list(range(5, 33, 4))  # [1, 5, 9, 13, 17, 21, 25, 29]
        
        for clients in client_counts:
            print(f"\nTesting with {clients} clients...")
            for rep in range(1, num_reps + 1):
                print(f"  Repetition {rep}/{num_reps}", end="", flush=True)

                # Start server
                server = subprocess.Popen([sys.executable, "server.py"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                time.sleep(2)  # Let server boot

                try:
                    elapsed = run_experiment(clients, rep)
                    writer.writerow([clients, rep, elapsed])
                    print(f" - {elapsed:.2f} ms")
                except Exception as e:
                    print(f" - FAILED: {e}")
                finally:
                    # Stop server
                    server.terminate()
                    try:
                        server.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()
                    time.sleep(1)  # Brief pause between experiments

    print(f"\nAll experiments completed. Results saved to results.csv")
    print("Run 'python3 plot_results.py' to generate the plot.")