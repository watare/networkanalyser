# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Network analysis toolkit for industrial protocols PTP (Precision Time Protocol) and IEC 61850 with AI-assisted diagnostics. The project consists of Python-based diagnostic tools that can be installed system-wide and integrated with OpenRouter AI for intelligent analysis.

## Architecture

- **ptp_diag.py**: Core PTP frame analyzer using linuxptp tools (ptp4l, pmc) for detailed PTP stack analysis
- **iec61850_diag.py**: IEC 61850 protocol analyzer detecting GOOSE, Sampled Values (SV), and MMS reports using Scapy
- **cli_chat.py**: Unified CLI providing AI-powered diagnostics integration with OpenRouter API

## Installation & Setup

```bash
# System installation (creates wrappers in /usr/local/bin)
sudo make install

# Manual dependency installation
sudo apt-get install linuxptp python3-venv
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env to add: OPENROUTER_API_KEY=your_key
```

## Common Commands

### Development & Testing
```bash
# Syntax check all Python files
make check

# Run diagnostic manually (development)
python3 ptp_diag.py -i eth0 -t 30
python3 iec61850_diag.py -i eth0
python3 cli_chat.py logs
python3 cli_chat.py chat

# Makefile shortcuts
make run-diagnostic IFACE=eth0 DURATION=30
make logs
make chat
make check-key
```

### Production Usage
```bash
# After installation, use system commands
sudo ptp-diag -i eth0
sudo iec61850-diag -i eth0
ptp-logs
ptp-chat
```

### Installation Management
```bash
make install    # Install to system
make uninstall  # Remove from system
```

## Key Implementation Details

- **Root privileges required**: Network analysis tools need sudo for raw packet capture
- **Virtual environments**: Each installed tool uses isolated Python venv in /opt/
- **Automatic .env loading**: CLI tools automatically load .env from script directory
- **Logging**: Diagnostic results written to diagnostic.log for AI analysis
- **Exit codes**: ptp_diag.py uses specific exit codes (0=OK, 1=warnings, 2=critical, 3=error)
- **Protocol specifics**: 
  - GOOSE frames use EtherType 0x88B8
  - SV frames use EtherType 0x88BA
  - MMS reports on TCP port 102

## Dependencies

- **System**: linuxptp, python3-venv
- **Python**: scapy>=2.5.0, python-dotenv>=1.0.0, requests>=2.31.0
- **Runtime**: OpenRouter API key for AI features