#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ptp_diag.py — PTP frames/stack analyzer based on linuxptp (ptp4l + pmc)
#
# Usage:
#   sudo ./ptp_diag.py -i eth0
#   sudo ./ptp_diag.py -i enp3s0 -t 25 --json
#
# Exit codes:
#   0 = OK/no critical issue
#   1 = warnings only
#   2 = critical issues / no GM / no PTP seen
#   3 = runtime error

import argparse, os, re, shlex, signal, subprocess, sys, tempfile, time, json

PMCID_CMDS = [
    "GET TIME_STATUS_NP",
    "GET DEFAULT_DATA_SET",
    "GET PARENT_DATA_SET",
    "GET TIME_PROPERTIES_DATA_SET",
    "GET PORT_DATA_SET_NP",
    "GET CLOCK_DESCRIPTION",
    "GET DOMAIN",
    "GET DELAY_MECHANISM",
    "GET LOG_SYNC_INTERVAL",
    "GET LOG_ANNOUNCE_INTERVAL",
    "GET LOG_MIN_PDELAY_REQ_INTERVAL",
    "GET SLAVE_ONLY",
]

def run(cmd, timeout=30, check=False, capture=True, input_text=None, env=None):
    """Run a shell command safely."""
    if capture:
        res = subprocess.run(cmd, input=input_text.encode() if input_text else None,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=timeout, check=check, env=env)
        return res.returncode, res.stdout.decode(errors="replace"), res.stderr.decode(errors="replace")
    else:
        res = subprocess.run(cmd, timeout=timeout, check=check, env=env)
        return res.returncode, "", ""

def require_root():
    if os.geteuid() != 0:
        print("ERROR: run as root (sudo).", file=sys.stderr)
        sys.exit(3)

def have(cmd):
    return subprocess.call(["/usr/bin/env", "bash", "-lc", f"command -v {shlex.quote(cmd)} >/dev/null 2>&1"]) == 0

def ensure_linuxptp():
    if have("ptp4l") and have("pmc"):
        return
    print("Installing linuxptp…")
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    run(["/usr/bin/env", "bash", "-lc", "apt-get update -qq"], timeout=600, env=env)
    rc, _, err = run(["/usr/bin/env", "bash", "-lc", "apt-get install -y -qq linuxptp"], timeout=600, env=env)
    if rc != 0:
        print("ERROR: linuxptp installation failed:\n" + err, file=sys.stderr)
        sys.exit(3)

def start_ptp4l(iface, transport_flag, uds_path, log_path, client_only=True, delay_auto=True):
    cfg = f"""[global]
use_syslog 0
logging_level 6
message_tag PTPDIAG
uds_address {uds_path}
clientOnly {1 if client_only else 0}
delay_mechanism {"Auto" if delay_auto else "E2E"}
[ {iface} ]
"""
    cfg_fd, cfg_path = tempfile.mkstemp(prefix="ptp4l-", suffix=".conf")
    with os.fdopen(cfg_fd, "w") as f:
        f.write(cfg)

    cmd = ["ptp4l", "-m", "-q", "-f", cfg_path, "-i", iface, "-S"]
    if transport_flag in ("-2", "-4", "-6"):
        cmd.insert(1, transport_flag)
    cmd.insert(1, "-A")

    logf = open(log_path, "w")
    proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, preexec_fn=os.setsid)
    return proc, cfg_path, logf

def stop_ptp4l(proc, logf, cfg_path):
    try: os.killpg(proc.pid, signal.SIGTERM)
    except Exception: pass
    try: proc.wait(timeout=5)
    except Exception:
        try: os.killpg(proc.pid, signal.SIGKILL)
        except Exception: pass
    try: logf.close()
    except Exception: pass
    try: os.unlink(cfg_path)
    except Exception: pass

def pmc_query(uds_path):
    input_text = "\n".join(PMCID_CMDS) + "\n"
    rc, out, err = run(["pmc", "-u", "-s", uds_path], timeout=10, input_text=input_text)
    if rc != 0 and not out:
        return None, err
    return out, None

def parse_pmc_output(text):
    data, current = {}, None
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        m = re.search(r"\b(RESPONSE|ANNOUNCE|MANAGEMENT)\b.*\b([A-Z0-9_]+)\b$", line)
        if m:
            current = m.group(2)
            data.setdefault(current, {})
            continue
        if current:
            kv = re.match(r"([A-Za-z0-9_]+)\s+(.+)$", line)
            if kv:
                k, v = kv.group(1), kv.group(2).strip()
                if v.lower() in ("true", "false"):
                    v = (v.lower() == "true")
                else:
                    try:
                        iv = int(v, 0) if v.startswith("0x") else int(v)
                        v = iv
                    except Exception:
                        v = v
                data[current][k] = v
    return data

def infer_transport(flag_used):
    return {"-2": "L2", "-4": "UDPv4", "-6": "UDPv6"}.get(flag_used, "Unknown")

def pick_profile(transport, domain, delay_mech, log_sync, log_announce, two_step):
    dm = (str(delay_mech) or "").upper()
    try: ls = int(log_sync)
    except: ls = None
    try: la = int(log_announce)
    except: la = None
    if transport == "L2" and dm == "P2P":
        if domain in (0, 1): return "IEC/IEEE 61850-9-3 (Power Utility Profile)"
        if domain in (24, ): return "ITU-T G.8275.1 (Telecom, full timing support)"
        return "L2 P2P (likely 9-3 or G.8275.1)"
    if transport in ("UDPv4", "UDPv6") and dm in ("E2E", "AUTO", "NONE"):
        if domain in (24, ): return "ITU-T G.8275.2 (Telecom, partial timing support)"
        if domain in (0, ): return "IEEE 1588 Default Profile"
        return "IP E2E (likely Default/G.8275.2)"
    return "Unknown/Mixed"

def expected_intervals(profile):
    if "9-3" in profile:
        return {"two_step": True, "log_sync": {-4, -3}, "log_announce": {0}, "delay_mech": "P2P"}
    if "G.8275.1" in profile:
        return {"two_step": True, "log_sync": {-4, -3}, "log_announce": {0}, "delay_mech": "P2P"}
    if "G.8275.2" in profile:
        return {"two_step": None, "log_sync": {-4, -3, -2}, "log_announce": {0}, "delay_mech": "E2E"}
    if "Default" in profile:
        return {"two_step": None, "log_sync": {-4, -3, -2, 0}, "log_announce": {0, 1}, "delay_mech": "E2E"}
    return {"two_step": None, "log_sync": set(), "log_announce": set(), "delay_mech": None}

def assess(data, transport):
    get = lambda s,k,d=None: data.get(s,{}).get(k, d)
    ts, dds, pds, tps, pnp, cd = data.get("TIME_STATUS_NP", {}), data.get("DEFAULT_DATA_SET", {}), \
        data.get("PARENT_DATA_SET", {}), data.get("TIME_PROPERTIES_DATA_SET", {}), \
        data.get("PORT_DATA_SET_NP", {}), data.get("CLOCK_DESCRIPTION", {})
    doms, dmech, lsi, lai, lpdi = data.get("DOMAIN", {}), data.get("DELAY_MECHANISM", {}), \
        data.get("LOG_SYNC_INTERVAL", {}), data.get("LOG_ANNOUNCE_INTERVAL", {}), \
        data.get("LOG_MIN_PDELAY_REQ_INTERVAL", {})
    domain = get("DOMAIN","domainNumber", get("DEFAULT_DATA_SET","domainNumber", 0))
    delay_mech = dmech.get("delay_mechanism", pnp.get("delay_mechanism", "Auto"))
    two_step = bool(pnp.get("twoStep", pnp.get("two_step", False)))
    log_sync = lsi.get("logSyncInterval", pnp.get("logSyncInterval"))
    log_announce = lai.get("logAnnounceInterval", pnp.get("logAnnounceInterval"))
    log_pdelay = lpdi.get("logMinPdelayReqInterval", pnp.get("logMinPdelayReqInterval"))
    gm_present, gm_id = ts.get("gmPresent", False), ts.get("gmIdentity", pds.get("grandmasterIdentity"))
    master_offset, mean_path_delay = ts.get("master_offset"), ts.get("meanPathDelay", ts.get("peerMeanPathDelay"))
    clock_class, time_traceable, freq_traceable = pds.get("grandmasterClockClass", dds.get("clockClass")), \
        tps.get("timeTraceable", None), tps.get("frequencyTraceable", None)
    prof_identity = cd.get("profileIdentity", pnp.get("profileIdentity"))
    profile = pick_profile(transport, int(domain) if str(domain).isdigit() else 0,
                           str(delay_mech), log_sync, log_announce, two_step)
    exp = expected_intervals(profile)
    warnings, critical = [], []
    if not gm_present:
        critical.append("No grandmaster detected on this transport/config.")
    if master_offset is not None:
        try:
            off = int(master_offset)
            if abs(off) > 10000000: critical.append(f"Master offset {off} ns (>10 ms).")
            elif abs(off) > 1000000: warnings.append(f"Master offset {off} ns (>1 ms).")
        except: pass
    if mean_path_delay is not None:
        try:
            mpd = int(mean_path_delay)
            if mpd > 5000000: warnings.append(f"Mean path delay {mpd} ns (>5 ms).")
        except: pass
    if exp["delay_mech"] and exp["delay_mech"] != str(delay_mech).upper():
        warnings.append(f"Delay mechanism is {delay_mech}, expected {exp['delay_mech']} for {profile}.")
    if exp["two_step"] is True and two_step is False:
        warnings.append(f"1-step observed; {profile} typically requires 2-step.")
    if log_sync is not None and exp["log_sync"]:
        try:
            if int(log_sync) not in exp["log_sync"]:
                warnings.append(f"logSyncInterval={log_sync} atypical for {profile}.")
        except: pass
    if log_announce is not None and exp["log_announce"]:
        try:
            if int(log_announce) not in exp["log_announce"]:
                warnings.append(f"logAnnounceInterval={log_announce} atypical for {profile}.")
        except: pass
    if time_traceable is False: warnings.append("timeTraceable=false.")
    if freq_traceable is False: warnings.append("frequencyTraceable=false.")
    if clock_class is not None:
        try:
            cc = int(clock_class)
            if cc >= 128: warnings.append(f"grandmasterClockClass={cc} (unspecified/holdover).")
        except: pass
    status = 2 if critical else (1 if warnings else 0)
    return {
        "transport": transport,
        "domain": domain,
        "delay_mechanism": str(delay_mech),
        "two_step": two_step,
        "log_sync": log_sync,
        "log_announce": log_announce,
        "log_pdelay": log_pdelay,
        "profile_guess": profile,
        "profile_identity_raw": prof_identity,
        "gm_present": gm_present,
        "gm_identity": gm_id,
        "grandmasterClockClass": clock_class,
        "timeTraceable": time_traceable,
        "frequencyTraceable": freq_traceable,
        "master_offset_ns": master_offset,
        "mean_path_delay_ns": mean_path_delay,
        "warnings": warnings,
        "critical": critical,
        "status_code": status,
    }

def try_probe(iface, transport_flag, dwell):
    uds = f"/var/run/ptp4l-analyze-{iface}-{transport_flag.replace('-', '')}"
    log = f"/tmp/ptp4l-analyze-{iface}-{transport_flag.replace('-', '')}.log"
    proc, cfg, logf = start_ptp4l(iface, transport_flag, uds, log)
    try:
        time.sleep(max(dwell, 5))
        out, err = pmc_query(uds)
        if out is None:
            return None, f"pmc error: {err}", proc, cfg, logf, uds, log
        data = parse_pmc_output(out)
        summary = assess(data, infer_transport(transport_flag))
        return summary, None, proc, cfg, logf, uds, log
    finally:
        stop_ptp4l(proc, logf, cfg)

def main():
    parser = argparse.ArgumentParser(description="PTP analyzer (ptp4l/pmc-based). Needs root.")
    parser.add_argument("-i", "--iface", required=True, help="Network interface (e.g., eth0)")
    parser.add_argument("-t", "--time", type=int, default=15, help="Observation time per transport (s)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    require_root()
    ensure_linuxptp()
    results, tried = [], []
    for tflag in ("-2", "-4", "-6"):
        tried.append(infer_transport(tflag))
        summary, err, *_ = try_probe(args.iface, tflag, args.time)
        if summary:
            results.append(summary)
            if summary["gm_present"]: break
    if not results:
        print("ERROR: No data collected.", file=sys.stderr)
        sys.exit(2)
    def score(s): return (1 if s["gm_present"] else 0, -(len(s["critical"])), -(len(s["warnings"])))
    best = sorted(results, key=score, reverse=True)[0]
    if args.json:
        print(json.dumps({"probe_order": tried, "best": best, "all": results}, indent=2))
    else:
        print("# PTP Diagnostic (linuxptp)")
        print(f"- Interface       : {args.iface}")
        print(f"- Transport tried : {', '.join(tried)}")
        print(f"- Selected        : {best['transport']}")
        print(f"- Profile (guess) : {best['profile_guess']}")
        print(f"- Domain          : {best['domain']}")
        print(f"- Delay mechanism : {best['delay_mechanism']}")
        print(f"- Two-step        : {best['two_step']}")
        print(f"- Intervals       : logSync={best['log_sync']} logAnnounce={best['log_announce']} logPdelay={best['log_pdelay']}")
        print(f"- GM present      : {best['gm_present']}  (id={best['gm_identity']})")
        print(f"- GM clockClass   : {best['grandmasterClockClass']}")
        print(f"- Traceability    : time={best['timeTraceable']} freq={best['frequencyTraceable']}")
        print(f"- Offsets         : master_offset={best['master_offset_ns']} ns mean_path_delay={best['mean_path_delay_ns']} ns")
        if best["profile_identity_raw"]:
            print(f"- profileIdentity : {best['profile_identity_raw']}")
        if best["critical"]:
            print("\nCRITICAL:")
            for c in best["critical"]: print(f"  - {c}")
        if best["warnings"]:
            print("\nWARNINGS:")
            for w in best["warnings"]: print(f"  - {w}")
        print(f"\nExit status: {best['status_code']} (0 OK, 1 warnings, 2 critical)")
    sys.exit(best["status_code"])

if __name__ == "__main__":
    main()

