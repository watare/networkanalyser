#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iec61850_diag.py — IEC 61850 frame analyzer.

Detects GOOSE and Sampled Values (SV) frames and counts them per
source address in 10-second windows. Also prints a message when an
MMS report is observed (TCP port 102 containing the word 'report').

Usage:
  sudo ./iec61850_diag.py -i eth0
"""

import argparse
import collections
import os
import sys

from scapy.all import Ether, Raw, TCP, sniff

GOOSE_ETHER_TYPE = 0x88B8
SV_ETHER_TYPE = 0x88BA
MMS_TCP_PORT = 102


def require_root():
    if os.geteuid() != 0:
        print("ERROR: run as root (sudo).", file=sys.stderr)
        sys.exit(1)


def analyze(iface):
    goose_counts = collections.Counter()
    sv_counts = collections.Counter()

    def handle(pkt):
        if Ether not in pkt:
            return
        src = pkt[Ether].src
        etype = pkt[Ether].type
        if etype == GOOSE_ETHER_TYPE:
            goose_counts[src] += 1
        elif etype == SV_ETHER_TYPE:
            sv_counts[src] += 1
        elif pkt.haslayer(TCP) and (
            pkt[TCP].sport == MMS_TCP_PORT or pkt[TCP].dport == MMS_TCP_PORT
        ):
            if pkt.haslayer(Raw) and b"report" in pkt[Raw].load.lower():
                print(f"MMS report from {src}")

    try:
        while True:
            sniff(iface=iface, prn=handle, store=False, timeout=10)
            if goose_counts or sv_counts:
                print("=== 10s summary ===")
                if goose_counts:
                    print("GOOSE frames:")
                    for addr, cnt in goose_counts.items():
                        print(f"  {addr}: {cnt}")
                if sv_counts:
                    print("SV frames:")
                    for addr, cnt in sv_counts.items():
                        print(f"  {addr}: {cnt}")
                goose_counts.clear()
                sv_counts.clear()
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(description="IEC 61850 frame analyzer")
    parser.add_argument("-i", "--iface", required=True, help="Network interface (e.g., eth0)")
    args = parser.parse_args()
    require_root()
    analyze(args.iface)


if __name__ == "__main__":
    main()
