# ⛏️ Mining Manager - BTC Toolkit All Miners

**Mining Manager** is a powerful, cross-platform desktop application designed to centralize the management of Bitcoin ASIC mining fleets. Built on top of the robust [pyasic](https://github.com/UpstreamData/pyasic) library, it provides a unified interface for over 500 miner models.

![Mining Manager UI](file:///C:/Users/alberto/.gemini/antigravity/brain/38a7a2ad-9b0d-4e71-a979-92b45485c5be/mining_manager_launch_1772019387574.webp)

## 🚀 Main Features

- **🔍 Smart Network Scan:** Automatically discover miners in your local network subnet.
- **📊 Real-time Monitoring:** View hashrate, temperature, uptime, and status for every miner.
- **🔄 Auto-Monitor:** Refreshes data every 5 minutes automatically.
- **🛠️ Bulk Configuration:** Update mining pools and workers for multiple miners simultaneously.
- **⚡ Remote Control:** Reboot selected miners or the entire fleet with a single click.
- **🔐 Global Credentials:** Unified password management for 25+ manufacturers via `config.json`.
- **🖥️ Modern GUI:** Intuitive and responsive interface built with CustomTkinter.

## 📁 Project Structure

- `main.py`: Entry point for the application.
- `miner_app/`: Core logic and UI components.
  - `core/scanner.py`: Asynchronous handling of pyasic operations.
  - `ui/app.py`: Graphical User Interface.
  - `config.json`: External configuration for passwords and network settings.
- `pyasic/`: Integrated library for ASIC communication.

## 🛠️ Supported Manufacturers

Thanks to `pyasic`, this toolkit supports:
- **Bitmain (Antminer)**
- **MicroBT (Whatsminer)**
- **Braiins OS / BOSminer**
- **Canaan (Avalonminer)**
- **Innosilicon**
- **Goldshell, IceRiver, EPic, Elphapex, HiveOn, VNish, and many more...**

## ⚙️ Configuration

You can manage default passwords for all manufacturers in `miner_app/config.json`. The application will use these credentials to connect to your miners automatically.

```json
{
  "passwords": {
    "antminer_web": "root",
    "whatsminer_rpc": "admin",
    "volcminer_ssh": "ltc@dog"
  },
  "network": {
    "ip_from": "192.168.1.1",
    "ip_to": "192.168.1.254"
  }
}
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ installed.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Hanksito/Btctoolkit-all-miners.git
   cd Btctoolkit-all-miners
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements_full.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## 📦 Portable Version
The project is ready for distribution. You can find the pre-compiled version in `dist/MiningManager/` which includes:
- `MiningManager.exe`
- Editable `config.json`
- All necessary dependencies.

---
**Disclaimer:** Use this tool at your own risk. Always ensure you have the correct permissions to access and configure miners on your network.
