# Network Analyser

Network analysis toolkit for industrial protocols PTP (Precision Time Protocol) and IEC 61850 with AI-assisted diagnostics.

## Features

- **PTP Analysis**: Core PTP frame analyzer using linuxptp tools (ptp4l, pmc) for detailed PTP stack analysis
- **IEC 61850 Protocol Analysis**: Detection of GOOSE, Sampled Values (SV), and MMS reports using Scapy
- **AI-Powered Diagnostics**: Unified CLI with OpenRouter API integration for intelligent analysis

## Scripts

- `ptp_diag.py`: PTP frame analysis via linuxptp tools
- `iec61850_diag.py`: IEC 61850 protocol analyzer (GOOSE, SV frames, MMS reports)  
- `cli_chat.py`: Unified CLI providing AI-powered diagnostics integration

## Installation

### System Installation
```bash
# Install system-wide (creates wrappers in /usr/local/bin)
sudo make install
```

This command installs `ptp-diag`, `iec61850-diag` and utilities `ptp-logs` and `ptp-chat` using isolated Python virtual environments.

### Manual Dependencies
```bash
sudo apt-get install linuxptp python3-venv
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and configure your OpenRouter API key:

```bash
cp .env.example .env
```

Edit `.env` to add your API key:
```
OPENROUTER_API_KEY=your_api_key
```

The `.env` file is automatically loaded by CLI tools and is not committed to the repository.

## Usage

### Production Usage (after installation)
```bash
# Run diagnostics (requires root for packet capture)
sudo ptp-diag -i eth0
sudo iec61850-diag -i eth0

# View logs and chat with AI
ptp-logs
ptp-chat
```

### Development Usage
```bash
# Manual diagnostic execution
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

### Quality Assurance
```bash
# Syntax check all Python files
make check
```

## AI Integration

### API Configuration
1. Get an API key from [OpenRouter](https://openrouter.ai)
2. Add it to your `.env` file:
   ```bash
   echo "OPENROUTER_API_KEY=\"your_key\"" > .env
   ```
3. The key is automatically loaded and never committed to the repository

### Complete Example Workflow
```bash
# 1. Run PTP diagnostic and generate logs
sudo ptp-diag -i eth0 -t 30

# 2. View diagnostic logs  
ptp-logs

# 3. Chat with AI about the results
ptp-chat
> What GOOSE packets look suspicious?
> Analyze the PTP synchronization quality
```

## Technical Details

- **Root privileges required**: Network analysis tools need sudo for raw packet capture
- **Virtual environments**: Each installed tool uses isolated Python venv in `/opt/`
- **Protocol specifics**: 
  - GOOSE frames use EtherType 0x88B8
  - SV frames use EtherType 0x88BA  
  - MMS reports on TCP port 102
- **Exit codes**: ptp_diag.py uses specific exit codes (0=OK, 1=warnings, 2=critical, 3=error)

## Dependencies

- **System**: linuxptp, python3-venv
- **Python**: scapy>=2.5.0, python-dotenv>=1.0.0, requests>=2.31.0
- **Runtime**: OpenRouter API key for AI features

## Installation Management
```bash
make install    # Install to system
make uninstall  # Remove from system
```