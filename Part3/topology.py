#!/usr/bin/env python3
"""
Mininet Topology for Greedy Client FCFS Analysis (Part 3)
- Creates a simple network with one server, one switch, and N clients.
- This setup is used by the experiment runner to simulate the network environment.
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
import json

class GreedyClientTopo(Topo):
    """
    Topology: 1 Server, 1 Switch, N Clients.
    Server IP: 10.0.0.100
    Client IPs: 10.0.0.1, 10.0.0.2, ..., 10.0.0.N
    """
    def __init__(self, num_clients=10, bw=10, delay='1ms'):
        super().__init__()

        # Add a central switch
        switch = self.addSwitch('s1', cls=OVSSwitch)

        # Add the server with a fixed IP address
        server = self.addHost('server', ip='10.0.0.100/24', cpu=0.1)
        self.addLink(server, switch, bw=bw, delay=delay)

        # Add clients with sequential IP addresses
        for i in range(1, num_clients + 1):
            client = self.addHost(f'client{i}', ip=f'10.0.0.{i}/24', cpu=0.1)
            self.addLink(client, switch, bw=bw, delay=delay)

def create_and_run_cli():
    """
    This function is executed when the script is run directly.
    It creates the network and starts the Mininet CLI for interactive testing.
    """
    setLogLevel('info')
    
    num_clients = 10
    try:
        with open('config.json') as f:
            config = json.load(f)
            num_clients = config.get('num_clients', 10)
    except FileNotFoundError:
        print("config.json not found, using default of 10 clients.")
    except Exception as e:
        print(f"Error reading config.json: {e}, using default of 10 clients.")
        
    print(f"Creating a network with 1 server and {num_clients} clients.")
    
    topo = GreedyClientTopo(num_clients)
    net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink, controller=None)
    net.start()

    print("\n--- Network is running. You can now use the Mininet CLI. ---")
    print("Example commands to run in the CLI:")
    print("  server python3 server.py &")
    print("  client1 python3 client.py --client-id client1 --greedy --c 5")
    print("  client2 python3 client.py --client-id client2")
    print("  exit")
    print("------------------------------------------------------------\n")

    CLI(net)
    
    print("--- Stopping network ---")
    net.stop()

if __name__ == '__main__':
    create_and_run_cli()
