#!/usr/bin/env python3
# Socket Programming Assignment - Experiment Runner
# Completed version of the starter code

import re
import time
import csv
import json
from pathlib import Path
from topo_wordcount import make_net

# Config
K_VALUES = [1, 2, 5, 10, 20, 50, 100]
RUNS_PER_K = 5
SERVER_CMD = "./server --config config.json"
CLIENT_CMD_TMPL = "./client --config config.json --quiet"
RESULTS_CSV = Path("results.csv")

def modify_config(key, value):
    """Modify a specific key in config.json"""
    config_path = Path("config.json")

    # Load existing config
    if config_path.exists():
        with config_path.open("r") as f:
            config = json.load(f)
    else:
        # Default config if file doesn't exist
        config = {
            "server_ip": "10.0.0.2",
            "server_port": 5000,
            "filename": "words.txt",
            "p": 0,
            "k": 5,
            "num_repetitions": 5
        }

    # Modify the specified key
    config[key] = value

    # Save back to file
    with config_path.open("w") as f:
        json.dump(config, f, indent=4)

    print(f"Updated config: {key} = {value}")

def main():
    print("Starting Socket Programming Experiments")
    print("=" * 40)

    # Prepare CSV
    if not RESULTS_CSV.exists():
        with RESULTS_CSV.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["k", "run", "elapsed_ms"])

    # Create and start network
    net = make_net()
    net.start()

    h1 = net.get('h1')  # client
    h2 = net.get('h2')  # server

    # Ensure words.txt exists (shared FS)
    if not Path("words.txt").exists():
        print("Creating default words.txt...")
        Path("words.txt").write_text("cat,bat,cat,dog,dog,emu,emu,emu,ant\n")

    # Start server
    print("Starting server on h2...")
    srv = h2.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
    time.sleep(1)  # give it a moment to bind

    try:
        total_experiments = len(K_VALUES) * RUNS_PER_K
        current_experiment = 0

        for k in K_VALUES:
            print(f"\nTesting k = {k}")

            for r in range(1, RUNS_PER_K + 1):
                current_experiment += 1
                print(f"  Run {r}/{RUNS_PER_K} (experiment {current_experiment}/{total_experiments})")

                # Update config for this k value
                modify_config("k", k)

                # Run client
                cmd = CLIENT_CMD_TMPL
                out = h1.cmd(cmd)

                # Parse ELAPSED_MS
                m = re.search(r"ELAPSED_MS:(\d+)", out)
                if not m:
                    print(f"[warn] No ELAPSED_MS found for k={k} run={r}. Raw:\n{out}")
                    continue

                ms = int(m.group(1))

                # Save result to CSV
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([k, r, ms])

                print(f"    k={k} run={r} elapsed_ms={ms}")

                # Small delay between runs
                time.sleep(0.2)

    finally:
        print("\nCleaning up...")
        srv.terminate()
        time.sleep(0.5)
        net.stop()

    print(f"\n✅ Experiments completed!")
    print(f"📊 Results saved to {RESULTS_CSV}")
    print("Run 'python3 plot_results.py' to generate plot")

if __name__ == "__main__":
    main()