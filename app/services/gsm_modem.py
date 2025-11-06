"""GSM Modem SMS service."""

from typing import Dict, List


class GSMModemService:
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.modem = None

    async def connect(self):
        """Connect to GSM modem."""
        try:
            from gsmmodem.modem import GsmModem

            self.modem = GsmModem(self.port, self.baudrate)
            self.modem.connect()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def send_sms(self, phone: str, message: str) -> Dict:
        """Send SMS via GSM modem."""
        if not self.modem:
            await self.connect()

        try:
            self.modem.sendSms(phone, message)
            return {"status": "sent", "phone": phone}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_messages(self) -> List[Dict]:
        """Get received SMS messages."""
        if not self.modem:
            await self.connect()

        try:
            messages = []
            for sms in self.modem.listStoredSms():
                messages.append(
                    {
                        "phone": sms.number,
                        "message": sms.text,
                        "time": sms.time.isoformat(),
                        "status": sms.status,
                    }
                )
            return messages
        except Exception as e:
            return [{"error": str(e)}]

    def disconnect(self):
        """Disconnect from modem."""
        if self.modem:
            self.modem.close()
