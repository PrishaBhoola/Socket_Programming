from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

DEFAULT_CLIENTS = 10

BANDWIDTH = 1  
DELAY = '0ms'
BUFFER_SIZE = 1000

class SimpleTopo(Topo):
    def __init__(self, num_clients=DEFAULT_CLIENTS):
        Topo.__init__(self)
        switch = self.addSwitch('s1', cls=OVSSwitch)
        server = self.addHost('server', ip='10.0.0.100')
        clients = []
        for i in range(num_clients):
            client = self.addHost(f'client{i+1}', ip=f'10.0.0.{i+1}')
            clients.append(client)
        self.addLink(server, switch, bw=BANDWIDTH)
        for client in clients:
            self.addLink(client, switch, bw=BANDWIDTH)

def create_network(num_clients=DEFAULT_CLIENTS):
    topo = SimpleTopo(num_clients)
    net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink)
    net.start()
    return net

if __name__ == '__main__':
    setLogLevel('info')
    num_clients = DEFAULT_CLIENTS
    try:
        import json
        with open('config.json') as f:
            config = json.load(f)
            num_clients = config.get('num_clients', DEFAULT_CLIENTS)
    except:
        pass

    net = create_network(num_clients)

    for h in net.hosts:
        print(f"  {h.name}: {h.IP()}")

    CLI(net)
    net.stop()
