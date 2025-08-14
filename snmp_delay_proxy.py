#!/usr/bin/env python3
import argparse, logging, signal, socket, sys, threading, time, random
from typing import Tuple

def parse_hostport(s: str) -> Tuple[str, int]:
    host, port = s.rsplit(":", 1)
    return host, int(port)

def snmp_brief(packet: bytes) -> str:
    """Minimal SNMP summary: community + PDU name."""
    try:
        idx = 2 + ((packet[1] & 0x7F) if (packet[1] & 0x80) else 0)  # skip outer length
        idx += 2 + packet[idx + 1]  # skip version INTEGER
        com_len = packet[idx + 1]
        community = packet[idx + 2 : idx + 2 + com_len].decode(errors="replace")
        idx += 2 + com_len
        pdu_tag = packet[idx]
        pdu_map = {
            0xA0: "GetRequest",
            0xA1: "GetNext",
            0xA2: "GetResponse",
            0xA3: "SetRequest",
            0xA4: "Trap",
            0xA5: "GetBulk",
        }
        pdu = pdu_map.get(pdu_tag, f"0x{pdu_tag:02X}")
        return f"community='{community}' PDU={pdu}"
    except Exception:
        return "Unparsed"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--listen", default="0.0.0.0:16100")
    p.add_argument("--dest",   default="127.0.0.1:161")
    p.add_argument("--delay",  type=float, default=0.0, help="Delay before forwarding in seconds (default 0.0)")
    p.add_argument("--drop-rate", type=float, default=0.0, help="Probability to drop a request (0.0-1.0)")
    p.add_argument("--timeout",type=float, default=2.0, help="Upstream response timeout in seconds (0 = blocking)")
    p.add_argument("--log",    default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"])
    args = p.parse_args()

    logging.basicConfig(level=getattr(logging, args.log), format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("snmp-delay-proxy")

    listen_host, listen_port = parse_hostport(args.listen)
    dest_host, dest_port     = parse_hostport(args.dest)
    dest = (dest_host, dest_port)
    eff_timeout = None if args.timeout <= 0 else args.timeout

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((listen_host, listen_port))

    stop = threading.Event()
    signal.signal(signal.SIGINT,  lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    stats = {"rx":0, "tx":0, "dropped":0, "timeouts":0, "errors":0}

    log.info("Listening on %s:%d -> %s:%d (delay=%.3fs drop-rate=%.2f timeout=%s)",
             listen_host, listen_port, dest_host, dest_port,
             args.delay, args.drop_rate,
             f"{eff_timeout:.1f}s" if eff_timeout is not None else "blocking")

    t_start = time.time()

    while not stop.is_set():
        try:
            sock.settimeout(0.5)
            pkt, client = sock.recvfrom(65535)
        except socket.timeout:
            continue
        except OSError:
            break

        stats["rx"] += 1
        summary = snmp_brief(pkt)
        log.info("SNMP %s:%d (%dB): %s", client[0], client[1], len(pkt), summary)

        if args.drop_rate > 0:
            r = random.random()
            if r < args.drop_rate:
                stats["dropped"] += 1
                log.info("Dropped request from %s:%d (p=%.2f, draw=%.3f)", client[0], client[1], args.drop_rate, r)
                continue

        if args.delay > 0:
            log.info("Delay %.3fs before forwarding to %s:%d", args.delay, dest_host, dest_port)
            time.sleep(args.delay)

        start = time.time()
        up = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        up.settimeout(eff_timeout)
        try:
            up.sendto(pkt, dest)
            resp, _ = up.recvfrom(65535)
            sock.sendto(resp, client)
            stats["tx"] += 1
            log.info("Response sent to %s:%d (%.1f ms)", client[0], client[1], (time.time() - start) * 1000.0)
        except socket.timeout:
            stats["timeouts"] += 1
            log.warning("Timeout after %s from %s:%d (client %s:%d)",
                        f"{eff_timeout:.1f}s" if eff_timeout is not None else "blocking",
                        dest_host, dest_port, client[0], client[1])
        except Exception as e:
            stats["errors"] += 1
            log.warning("Error for %s:%d: %s", client[0], client[1], e)
        finally:
            up.close()

    sock.close()

    elapsed = max(0.0, time.time() - t_start)
    rx_rate = (stats["rx"] / elapsed) if elapsed > 0 else 0.0
    tx_rate = (stats["tx"] / elapsed) if elapsed > 0 else 0.0
    drop_pct = (100.0 * stats["dropped"] / stats["rx"]) if stats["rx"] > 0 else 0.0

    log.info(
        "Stats: rx=%d tx=%d dropped=%d (%.2f%%) timeouts=%d errors=%d elapsed=%.3fs rx_rate=%.2f/s tx_rate=%.2f/s",
        stats["rx"], stats["tx"], stats["dropped"], drop_pct, stats["timeouts"], stats["errors"],
        elapsed, rx_rate, tx_rate
    )

if __name__ == "__main__":
    sys.exit(main())
