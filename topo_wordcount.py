#!/usr/bin/env python3
"""
Network topology for word counting assignment
Simple topology with two hosts connected by a switch
"""

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel

class WordCountTopo(Topo):
    """Simple topology for word counting experiments"""

    def build(self):
        # Add hosts
        h1 = self.addHost('h1', ip='10.0.0.1/24')  # Client
        h2 = self.addHost('h2', ip='10.0.0.2/24')  # Server

        # Add switch
        s1 = self.addSwitch('s1')

        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s1)

def make_net():
    """Create and return a Mininet network instance"""
    # Set log level to reduce output
    setLogLevel('warning')

    # Create topology
    topo = WordCountTopo()

    # Create network
    net = Mininet(topo=topo, controller=OVSController, autoSetMacs=True, autoStaticArp=True)

    return net

# For standalone testing
def main():
    """Test the topology"""
    print("Testing word count topology...")

    net = make_net()
    net.start()

    print("Network started successfully!")
    print("Hosts:")
    for host in net.hosts:
        print(f"  {host.name}: {host.IP()}")

    # Test connectivity
    print("\nTesting connectivity...")
    result = net.pingAll()

    if result == 0:
        print("✅ All hosts can communicate")
    else:
        print("❌ Connectivity issues detected")

    # Start CLI for manual testing (optional)
    # CLI(net)

    net.stop()
    print("Network stopped")

if __name__ == "__main__":
    main()