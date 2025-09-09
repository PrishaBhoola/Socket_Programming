import re
import time
import csv
import json
from pathlib import Path
from topo_wordcount import make_net

K_VALUES = [1, 2, 4, 8, 12, 16, 20, 24, 32, 48]
RUNS_PER_K = 5
SERVER_CMD = "./server --config config.json"
CLIENT_CMD_TMPL = "./client --config config.json --quiet"
RESULTS_CSV = Path("results.csv")

def modify_config(key, value):
    config_path = Path("config.json")

    if config_path.exists():
        with config_path.open("r") as f:
            config = json.load(f)
    else:
        config = {
            "server_ip": "10.0.0.2",
            "server_port": 5000,
            "filename": "words.txt",
            "p": 0,
            "k": 5,
            "num_repetitions": 5
        }

    config[key] = value

    with config_path.open("w") as f:
        json.dump(config, f, indent=4)

def main():
    if not RESULTS_CSV.exists():
        with RESULTS_CSV.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["k", "run", "elapsed_ms"])

    net = make_net()
    net.start()

    h1 = net.get('h1') 
    h2 = net.get('h2') 

    if not Path("words.txt").exists():
        Path("words.txt").write_text("cat,bat,cat,dog,dog,emu,emu,emu,ant\n")

    srv = h2.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
    time.sleep(1)  

    try:
        total_experiments = len(K_VALUES) * RUNS_PER_K
        current_experiment = 0

        for k in K_VALUES:
            for r in range(1, RUNS_PER_K + 1):
                current_experiment += 1
                modify_config("k", k)
                cmd = CLIENT_CMD_TMPL
                out = h1.cmd(cmd)

                m = re.search(r"ELAPSED_MS:(\d+)", out)
                if not m:
                    print(f"[warn] No ELAPSED_MS found for k={k} run={r}. Raw:\n{out}")
                    continue

                ms = int(m.group(1))

                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([k, r, ms])
                time.sleep(0.2)

    finally:
        srv.terminate()
        time.sleep(0.5)
        net.stop()

if __name__ == "__main__":
    main()