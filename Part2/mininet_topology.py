#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost, Host
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
import json
import sys
import time
import subprocess

class ClientServerTopo(Topo):
    """Simple topology with one server and multiple client hosts"""
    
    def build(self, num_clients=5):
        # Add switch
        switch = self.addSwitch('s1')
        
        # Add server host
        server = self.addHost('server', ip='10.0.0.2/24')
        self.addLink(server, switch)
        
        # Add client hosts
        for i in range(1, num_clients + 1):
            client = self.addHost(f'client{i}', ip=f'10.0.0.{i+2}/24')
            self.addLink(client, switch)

def run_mininet_experiment():
    """Run the experiment in Mininet environment"""
    
    # Load config
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found")
        sys.exit(1)
    
    num_clients = config.get("num_clients", 5)
    
    print(f"Setting up Mininet topology with {num_clients} clients...")
    
    # Create topology
    topo = ClientServerTopo(num_clients=num_clients)
    
    # Create network
    net = Mininet(topo=topo, host=Host, link=TCLink)
    net.start()
    
    print("Network started. Topology:")
    dumpNodeConnections(net.hosts)
    
    try:
        # Get hosts
        server = net.get('server')
        
        # Copy files to server
        print("Copying files to server...")
        server.cmd('mkdir -p /tmp/experiment')
        for filename in ['server.py', 'config.json', 'words.txt']:
            server.cmd(f'cp {filename} /tmp/experiment/ 2>/dev/null || echo "Warning: {filename} not found"')
        
        # Start server
        print("Starting server...")
        server.cmd('cd /tmp/experiment && python3 server.py &')
        time.sleep(3)  # Give server time to start
        
        # Copy files to clients and run experiment
        client_processes = []
        print(f"Starting {num_clients} clients...")
        
        for i in range(1, num_clients + 1):
            client = net.get(f'client{i}')
            # Copy files to client
            client.cmd('mkdir -p /tmp/experiment')
            for filename in ['client.py', 'config.json']:
                client.cmd(f'cp {filename} /tmp/experiment/ 2>/dev/null || echo "Warning: {filename} not found"')
            
            # Start client
            client.cmd(f'cd /tmp/experiment && python3 client.py > /tmp/client{i}_output.txt 2>&1 &')
        
        # Wait for clients to complete
        print("Waiting for clients to complete...")
        time.sleep(10)  # Adjust based on expected completion time
        
        # Collect results
        print("Collecting results...")
        for i in range(1, num_clients + 1):
            client = net.get(f'client{i}')
            output = client.cmd('cat /tmp/client{}_output.txt'.format(i))
            print(f"Client {i} output:")
            print(output)
        
        # Optional: Start CLI for manual testing
        print("Starting Mininet CLI. Type 'exit' to quit.")
        CLI(net)
        
    except KeyboardInterrupt:
        print("Experiment interrupted by user")
    except Exception as e:
        print(f"Error during experiment: {e}")
    finally:
        print("Stopping network...")
        net.stop()

def run_mininet_experiments():
    """Run multiple experiments for plotting"""
    
    # Load config
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found")
        sys.exit(1)
    
    num_reps = config.get("num_repetitions", 5)
    
    print(f"Running Mininet experiments with {num_reps} repetitions each...")
    print("Testing concurrent clients from 1 to 32 (incremented by 4)...")
    
    import csv
    
    # Create results file
    with open("results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["clients", "repetition", "completion_time"])
        
        # Test from 1 to 32 clients, incremented by 4
        client_counts = [1] + list(range(5, 33, 4))  # [1, 5, 9, 13, 17, 21, 25, 29]
        
        for clients in client_counts:
            print(f"\nTesting with {clients} clients...")
            
            for rep in range(1, num_reps + 1):
                print(f"  Repetition {rep}/{num_reps}...")
                
                # Update config for this experiment
                config["num_clients"] = clients
                with open("config.json", "w") as config_file:
                    json.dump(config, config_file, indent=2)
                
                # Create topology
                topo = ClientServerTopo(num_clients=clients)
                net = Mininet(topo=topo, host=Host, link=TCLink)
                net.start()
                
                try:
                    # Record start time
                    start_time = time.time()
                    
                    # Get server and setup
                    server = net.get('server')
                    server.cmd('mkdir -p /tmp/experiment')
                    for filename in ['server.py', 'config.json', 'words.txt']:
                        server.cmd(f'cp {filename} /tmp/experiment/ 2>/dev/null')
                    
                    # Start server
                    server.cmd('cd /tmp/experiment && python3 server.py &')
                    time.sleep(2)
                    
                    # Start all clients simultaneously
                    for i in range(1, clients + 1):
                        client = net.get(f'client{i}')
                        client.cmd('mkdir -p /tmp/experiment')
                        for filename in ['client.py', 'config.json']:
                            client.cmd(f'cp {filename} /tmp/experiment/ 2>/dev/null')
                        client.cmd(f'cd /tmp/experiment && python3 client.py > /tmp/client{i}_output.txt 2>&1 &')
                    
                    # Wait for all clients to complete
                    time.sleep(8)  # Adjust based on expected completion time
                    
                    # Record end time
                    end_time = time.time()
                    elapsed_ms = (end_time - start_time) * 1000
                    
                    writer.writerow([clients, rep, elapsed_ms])
                    print(f"    Completed in {elapsed_ms:.2f} ms")
                    
                except Exception as e:
                    print(f"    FAILED: {e}")
                finally:
                    net.stop()
                    time.sleep(1)  # Brief pause between experiments
    
    print(f"\nAll experiments completed. Results saved to results.csv")
    print("Run 'python3 plot_results.py' to generate the plot.")

if __name__ == "__main__":
    setLogLevel('info')
    
    if len(sys.argv) > 1 and sys.argv[1] == "plot":
        run_mininet_experiments()
    else:
        run_mininet_experiment()