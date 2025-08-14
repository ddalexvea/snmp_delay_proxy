# snmp_delay_proxy
to simulate SNMP request delay and packets drops

### Help
````
./snmp_delay_proxyV2.py -h
usage: snmp_delay_proxyV2.py [-h] [--listen LISTEN] [--dest DEST] [--delay DELAY] [--drop-rate DROP_RATE]
                             [--timeout TIMEOUT]

options:
  -h, --help            show this help message and exit
  --listen LISTEN
  --dest DEST
  --delay DELAY         Delay before forwarding in seconds (default 0.0)
  --drop-rate DROP_RATE
                        Probability to drop a request (0.0-1.0)
  --timeout TIMEOUT     Upstream response timeout in seconds (0 = blocking)
````

