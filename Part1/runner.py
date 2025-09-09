import json, os, time, pathlib

from topo_wordcount import make_net

K = int(os.environ.get("K", "5"))
P = int(os.environ.get("P", "0"))

cfg = json.loads(pathlib.Path("config.json").read_text())
cfg["p"] = P
pathlib.Path("demo_config.json").write_text(json.dumps(cfg, indent=4))

net = make_net(); net.start()
h1, h2 = net.get('h1'), net.get('h2')

srv = h2.popen("./server --config demo_config.json", shell=True)
time.sleep(0.5)

srv.terminate(); time.sleep(0.2); net.stop()