#!/usr/bin/env python3
"""
Mininet topology for Greedy Client FCFS Analysis (Part 3)
Creates network with server and multiple clients for fairness testing
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

# Default configuration
DEFAULT_CLIENTS = 10
BANDWIDTH = 1  # Mbps
DELAY = '0ms'

class GreedyClientTopo(Topo):
    """Topology for greedy client fairness analysis"""

    def __init__(self, num_clients=DEFAULT_CLIENTS):
        Topo.__init__(self)

        # Create switch
        switch = self.addSwitch('s1', cls=OVSSwitch)

        # Create server at fixed IP
        server = self.addHost('server', ip='10.0.0.100/24')

        # Create clients with sequential IPs
        for i in range(num_clients):
            client = self.addHost(f'client{i+1}', ip=f'10.0.0.{i+1}/24')

        # Connect server to switch
        self.addLink(server, switch, bw=BANDWIDTH, delay=DELAY)

        # Connect all clients to switch
        for i in range(num_clients):
            client_name = f'client{i+1}'
            self.addLink(client_name, switch, bw=BANDWIDTH, delay=DELAY)

def create_network(num_clients=DEFAULT_CLIENTS):
    """Create and start the network"""
    print(f"Creating greedy client analysis network")
    print(f"Server: 10.0.0.100")
    print(f"Clients: 10.0.0.1 to 10.0.0.{num_clients}")
    print(f"Link bandwidth: {BANDWIDTH} Mbps")

    topo = GreedyClientTopo(num_clients)
    net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink)
    net.start()

    return net

if __name__ == '__main__':
    setLogLevel('info')

    # Get number of clients from config or use default
    num_clients = DEFAULT_CLIENTS
    try:
        import json
        with open('config.json') as f:
            config = json.load(f)
            num_clients = config.get('num_clients', DEFAULT_CLIENTS)
    except:
        pass

    print(f"Creating network for greedy client analysis with {num_clients} clients")

    # Create network
    net = create_network(num_clients)

    print("Network created successfully!")
    print("Hosts:")
    for h in net.hosts:
        print(f"  {h.name}: {h.IP()}")

    print("\nStarting Mininet CLI...")
    print("You can now run:")
    print("  server python3 server.py &")
    print("  client1 python3 client.py --client-id client1 --greedy --c 10")
    print("  client2 python3 client.py --client-id client2")
    print("  exit")

    CLI(net)
    net.stop()
