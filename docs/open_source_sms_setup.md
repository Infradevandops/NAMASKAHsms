# Open Source SMS Verification Setup

## 1. Android SMS Gateway
**Tool**: SMS Gateway API (Free Android App)
- Install app on Android phone
- Exposes REST API for SMS
- Webhook support for incoming SMS
- Cost: Free (only SIM card costs)

## 2. GSM Modem + Python
**Tools**: 
- `python-gsmmodem` library
- `pyserial` for modem communication
- USB GSM modem (Huawei E3372, etc.)

## 3. Gammu SMS Daemon
**Tool**: Gammu + Gammu SMSD
- Open source SMS gateway
- Supports multiple modems
- Database integration
- Web interface available

## 4. Kannel SMS Gateway
**Tool**: Kannel (Open Source WAP/SMS Gateway)
- Professional SMS gateway
- Supports multiple connections
- HTTP API interface
- Used by telecom operators

## 5. PlaySMS Platform
**Tool**: PlaySMS (Open Source SMS Management)
- Complete SMS platform
- Web interface
- API support
- Multi-user system

## Implementation Options

### Option 1: Android Phone Gateway
```bash
# Install SMS Gateway app on Android
# Configure webhook URL: https://yourapi.com/sms/receive
# Send SMS via HTTP API
```

### Option 2: GSM Modem + Python
```python
# Install: pip install python-gsmmodem
from gsmmodem.modem import GsmModem

modem = GsmModem('/dev/ttyUSB0', 115200)
modem.connect()
modem.sendSms('+1234567890', 'Your code: 123456')
```

### Option 3: Gammu Setup
```bash
# Install Gammu
sudo apt-get install gammu gammu-smsd

# Configure /etc/gammu-smsdrc
# Start daemon
sudo systemctl start gammu-smsd
```