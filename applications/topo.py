#!/usr/bin/python
from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
import time
setLogLevel('info')

net = Containernet(controller=Controller)

info('*** Adding controller\n')
net.addController('c0')

info('*** Adding docker containers\n')
A = net.addDocker('A', ip='10.0.0.251', ports=[8766], dimage="server_app", volumes=["logsa:/app/log"])
B = net.addDocker('B', ip='10.0.0.252', ports=[8766], dimage="client_app", volumes=["logsb:/app/log"])
C = net.addDocker('C', ip='10.0.0.253', ports=[8766], dimage="client_app", volumes=["logsc:/app/log"])

A.cmd("python", "-u", "app.py A false", "> ./log/logs", "&")
B.cmd("python", "-u", "app.py B true", "> ./log/logs", "&")
C.cmd("python", "-u", "app.py", "> ./log/logs", "&")

info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
s3 = net.addSwitch('s3')
s4 = net.addSwitch('s4')

info('*** Creating links\n')
net.addLink(s1, s4, cls=TCLink, delay='100ms', bw=1)
net.addLink(s2, s4, cls=TCLink, delay='100ms', bw=1)
net.addLink(s3, s4, cls=TCLink, delay='100ms', bw=1)

net.addLink(A, s1)
net.addLink(B, s2)
net.addLink(C, s3)

info('*** Starting network\n')
net.start()

info('*** Testing connectivity\n')
net.ping([A, B, C])

info('*** Running CLI\n')
CLI(net)

info('*** Stopping network')
net.stop()
