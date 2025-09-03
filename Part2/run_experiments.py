import subprocess
import sys
import time
import csv
import json

def run_experiment(num_clients, repetition):
    start_time = time.time()

    processes = [
        subprocess.Popen([sys.executable, 'client.py'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        for _ in range(num_clients)
    ]

    for proc in processes:
        proc.wait()

    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    return elapsed_ms


if __name__ == "__main__":
    # Load config
    with open("config.json") as f:
        config = json.load(f)
    num_reps = config["num_repetitions"]

    print(f"Running experiments with {num_reps} repetitions each...")

    with open("results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["clients", "repetition", "completion_time"])

        for clients in [1, 2, 5, 10, 20]:
            print(f"Testing with {clients} clients...")
            for rep in range(1, num_reps + 1):
                print(f"  Repetition {rep}/{num_reps}")

                # start server
                server = subprocess.Popen([sys.executable, "server.py"])
                time.sleep(2)  # let server boot

                elapsed = run_experiment(clients, rep)
                writer.writerow([clients, rep, elapsed])

                server.terminate()
                time.sleep(1)

    print("All experiments completed. Results saved to results.csv")
