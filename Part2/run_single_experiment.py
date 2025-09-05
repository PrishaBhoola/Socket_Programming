import subprocess
import sys
import time
import json
import os

def run_single_experiment():
    """Run a single experiment with the configured number of clients."""
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

    num_clients = config.get("num_clients", 1)
    
    print(f"Running single experiment with {num_clients} clients...")
    
    # Record start time
    start_time = time.time()
    
    # Launch all clients simultaneously
    processes = []
    for i in range(num_clients):
        proc = subprocess.Popen(
            [sys.executable, 'client.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(proc)
    
    # Wait for all clients to complete and collect their outputs
    client_outputs = []
    for i, proc in enumerate(processes):
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            client_outputs.append(stdout.decode())
            print(f"Client {i+1} completed successfully")
        else:
            print(f"Client {i+1} failed with error: {stderr.decode()}")
    
    # Record end time
    end_time = time.time()
    total_elapsed_ms = (end_time - start_time) * 1000
    
    # Print summary
    print(f"\nExperiment Summary:")
    print(f"Total clients: {num_clients}")
    print(f"Successful clients: {len(client_outputs)}")
    print(f"Total experiment time: {total_elapsed_ms:.3f} ms")
    
    # Print individual client results
    for i, output in enumerate(client_outputs):
        print(f"\nClient {i+1} output:")
        print(output.strip())

if __name__ == "__main__":
    run_single_experiment()