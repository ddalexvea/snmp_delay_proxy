# snmp_delay_proxy
A **tiny SNMP UDP proxy** to simulate network conditions and inspect requests.
It listens on a local UDP port, optionally delays or drops requests, forwards them to a real SNMP agent, and relays responses back.
Logs are human-friendly: community string + PDU type, plus a final stats line with elapsed time and rates.

No external dependencies. Python standard library only.

### Features

- UDP proxy for SNMP (v1/v2c-style messages)
- Delay injection (fixed seconds; default 0.0)
- Packet drop by probability (--drop-rate)
- Best-effort request summary: community='<value>' PDU=<GetRequest|GetNext|GetBulk|...>
- Timeout control for upstream agent (--timeout, 0 = block/wait forever)
- Clean shutdown via Ctrl-C with final stats + elapsed time

### Help
````
./snmp_delay_proxyV2.py --help
usage: snmp_delay_proxyV2.py [-h] [--listen LISTEN] [--dest DEST] [--delay DELAY] [--drop-rate DROP_RATE]
                             [--timeout TIMEOUT] [--log {DEBUG,INFO,WARNING,ERROR}]

options:
  -h, --help            show this help message and exit
  --listen LISTEN
  --dest DEST
  --delay DELAY         Delay before forwarding in seconds (default 0.0)
  --drop-rate DROP_RATE
                        Probability to drop a request (0.0-1.0)
  --timeout TIMEOUT     Upstream response timeout in seconds (0 = blocking)
  --log {DEBUG,INFO,WARNING,ERROR}
````


### Examples
1) Default (no delay/drop):
````
./snmp_delay_proxy.py
````
2) 10% drops to test resilience:
````
./snmp_delay_proxy.py --drop-rate 0.10
````
3) Add 5s latency and longer wait for slow agent:
````
./snmp_delay_proxy.py --delay 5 --timeout 10
````

### Sample Output
````
2025-08-14 21:40:13 INFO Listening on 0.0.0.0:16100 -> 127.0.0.1:161 (delay=0.000s drop-rate=0.00 timeout=2.0s)
2025-08-14 21:40:15 INFO SNMP 127.0.0.1:60149 (36B): community='public' PDU=GetRequest
2025-08-14 21:40:15 INFO Response sent to 127.0.0.1:60149 (11.8 ms)
...
2025-08-14 21:55:15 INFO Stats: rx=9669 tx=9669 dropped=0 (0.00%) timeouts=0 errors=0 elapsed=120.532s rx_rate=80.20/s tx_rate=80.20/s
````


