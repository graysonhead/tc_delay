tc_delay
========

tc_delay is a script that automates creating netem qdiscs in the linux kernel.

Specifically, it allows you to create groups of IPs that have netem arguments applied to them.

This is useful when you are trying to simulate the behavior of a program on WAN connections (or connections with various 
defects) but the servers in question are on reliable connections and/or in the same subnet.

For instance, given the following config:
```.yaml
interface: wlp2s0
groups:
  - name: Group1
    ips:
      - 10.5.5.5/32
      - 10.5.5.4/32
    netem_args: "delay 100ms 50ms 25% loss random 1%"
  - name: Group2
    ips:
      - 8.8.8.8/32
    netem_args: "delay 1000ms"
```
Any traffic from this host to 10.5.5.5 or 10.5.5.4 will have 100ms of additional latency with 50ms of jitter at 25% correlation 
and 1% random packet loss.

Any traffic from this host to 8.8.8.8 will have 1000ms of additional latency.

For additional netem options, see here: https://man7.org/linux/man-pages/man8/tc-netem.8.html


The configuration file is applied in the following example(note that 'reload' and 'delete' actions will destroy the root
qdisc, removing any traffic shaping rules present on the host):
```
$ tc_delay --config ./example_configs/example.yaml --action reload
Executing command: tc qdisc del dev wlp2s0 root
Executing command: tc qdisc add dev wlp2s0 root handle 1: htb
Executing command: tc class add dev wlp2s0 parent 1: classid 1:1 htb rate 1000Mbps
Executing command: tc class add dev wlp2s0 parent 1:1 classid 1:2 htb rate 1000Mbps
Executing command: tc qdisc add dev wlp2s0 handle 2: parent 1:2 netem delay 100ms 50ms 25% loss random 1%
Executing command: tc filter add dev wlp2s0 pref 2 protocol ip parent 1:0 u32 match ip dst 10.5.5.5/32 flowid 1:2
Executing command: tc filter add dev wlp2s0 pref 2 protocol ip parent 1:0 u32 match ip dst 10.5.5.4/32 flowid 1:2
Executing command: tc class add dev wlp2s0 parent 1:1 classid 1:3 htb rate 1000Mbps
Executing command: tc qdisc add dev wlp2s0 handle 3: parent 1:3 netem delay 1000ms
Executing command: tc filter add dev wlp2s0 pref 3 protocol ip parent 1:0 u32 match ip dst 8.8.8.8/32 flowid 1:3
```

You can also purge the root qdisc (effectively cleaning all tc rules) using the action 'delete', as well as deleting and
 then creating in one step with 'relaod'.