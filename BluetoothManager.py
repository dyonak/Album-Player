"""
Bluetooth device management for Album Player.

Provides scanning, pairing, connecting, and disconnecting
Bluetooth audio devices using bluetoothctl.
"""

import subprocess
import re
import time
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class BluetoothDevice:
    """Represents a Bluetooth device."""
    address: str
    name: str
    paired: bool = False
    connected: bool = False
    trusted: bool = False


class BluetoothManager:
    """Manages Bluetooth devices via bluetoothctl."""

    def __init__(self):
        self._check_bluetooth_available()

    def _check_bluetooth_available(self) -> bool:
        """Check if Bluetooth is available on this system."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _run_bluetoothctl_cmd(self, command: str, timeout: int = 10) -> str:
        """Run a single bluetoothctl command."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "--", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            print(f"Bluetooth error: {e}")
            return ""

    def power_on(self) -> bool:
        """Turn on Bluetooth adapter."""
        output = self._run_bluetoothctl_cmd("power on")
        return "succeeded" in output.lower() or "yes" in output.lower()

    def power_off(self) -> bool:
        """Turn off Bluetooth adapter."""
        output = self._run_bluetoothctl_cmd("power off")
        return "succeeded" in output.lower()

    def is_powered(self) -> bool:
        """Check if Bluetooth adapter is powered on."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "Powered: yes" in result.stdout
        except:
            return False

    def scan(self, duration: int = 10) -> List[BluetoothDevice]:
        """
        Scan for nearby Bluetooth devices.

        Args:
            duration: How long to scan in seconds

        Returns:
            List of discovered devices
        """
        print(f"Starting Bluetooth scan for {duration} seconds...")

        # Start scan using a background process
        try:
            # Start bluetoothctl with scan on, let it run for duration
            proc = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send scan on command
            proc.stdin.write("scan on\n")
            proc.stdin.flush()

            # Wait for scan duration
            time.sleep(duration)

            # Send scan off and quit
            proc.stdin.write("scan off\n")
            proc.stdin.write("quit\n")
            proc.stdin.flush()

            # Wait for process to finish
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        except Exception as e:
            print(f"Scan error: {e}")

        print("Scan complete, getting devices...")
        return self.get_devices()

    def get_devices(self) -> List[BluetoothDevice]:
        """Get list of known Bluetooth devices."""
        devices = []

        try:
            # Get all devices
            result = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )

            print(f"Raw devices output: {result.stdout}")

            # Parse output: "Device XX:XX:XX:XX:XX:XX Device Name"
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                match = re.match(r'Device\s+([0-9A-Fa-f:]+)\s+(.+)', line, re.IGNORECASE)
                if match:
                    address = match.group(1)
                    name = match.group(2)

                    # Get device info
                    info = self._get_device_info(address)

                    devices.append(BluetoothDevice(
                        address=address,
                        name=name,
                        paired=info.get('paired', False),
                        connected=info.get('connected', False),
                        trusted=info.get('trusted', False)
                    ))
                    print(f"Found device: {name} ({address})")
        except Exception as e:
            print(f"Error getting devices: {e}")

        print(f"Total devices found: {len(devices)}")
        return devices

    def _get_device_info(self, address: str) -> Dict:
        """Get detailed info about a device."""
        info = {'paired': False, 'connected': False, 'trusted': False}

        try:
            result = subprocess.run(
                ["bluetoothctl", "info", address],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout
            info['paired'] = "Paired: yes" in output
            info['connected'] = "Connected: yes" in output
            info['trusted'] = "Trusted: yes" in output

        except:
            pass

        return info

    def get_paired_devices(self) -> List[BluetoothDevice]:
        """Get only paired devices."""
        return [d for d in self.get_devices() if d.paired]

    def get_connected_device(self) -> Optional[BluetoothDevice]:
        """Get the currently connected device, if any."""
        for device in self.get_devices():
            if device.connected:
                return device
        return None

    def pair(self, address: str) -> bool:
        """
        Pair with a device.

        Args:
            address: Bluetooth MAC address

        Returns:
            True if pairing succeeded
        """
        try:
            proc = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send pair command
            proc.stdin.write(f"pair {address}\n")
            proc.stdin.flush()

            # Wait for pairing
            time.sleep(5)

            # Trust the device
            proc.stdin.write(f"trust {address}\n")
            proc.stdin.flush()
            time.sleep(1)

            proc.stdin.write("quit\n")
            proc.stdin.flush()

            stdout, stderr = proc.communicate(timeout=10)
            output = stdout + stderr

            success = "pairing successful" in output.lower() or "already paired" in output.lower()
            return success

        except Exception as e:
            print(f"Pair error: {e}")
            return False

    def connect(self, address: str) -> bool:
        """
        Connect to a paired device.

        Args:
            address: Bluetooth MAC address

        Returns:
            True if connection succeeded
        """
        try:
            proc = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            proc.stdin.write(f"connect {address}\n")
            proc.stdin.flush()

            time.sleep(5)

            proc.stdin.write("quit\n")
            proc.stdin.flush()

            stdout, stderr = proc.communicate(timeout=10)
            output = stdout + stderr

            return "connection successful" in output.lower() or "connected: yes" in output.lower()

        except Exception as e:
            print(f"Connect error: {e}")
            return False

    def disconnect(self, address: str) -> bool:
        """
        Disconnect from a device.

        Args:
            address: Bluetooth MAC address

        Returns:
            True if disconnection succeeded
        """
        try:
            result = subprocess.run(
                ["bluetoothctl", "disconnect", address],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout + result.stderr
            return "successful" in output.lower() or "disconnected" in output.lower()
        except Exception as e:
            print(f"Disconnect error: {e}")
            return False

    def remove(self, address: str) -> bool:
        """
        Remove/unpair a device.

        Args:
            address: Bluetooth MAC address

        Returns:
            True if removal succeeded
        """
        try:
            result = subprocess.run(
                ["bluetoothctl", "remove", address],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout + result.stderr
            return "removed" in output.lower() or "not available" in output.lower()
        except Exception as e:
            print(f"Remove error: {e}")
            return False

    def set_discoverable(self, enabled: bool = True, timeout: int = 180) -> bool:
        """
        Set the Pi to be discoverable by other devices.

        Args:
            enabled: Whether to enable discoverable mode
            timeout: How long to stay discoverable (seconds)
        """
        try:
            if enabled:
                subprocess.run(["bluetoothctl", "discoverable-timeout", str(timeout)], timeout=5)
                result = subprocess.run(["bluetoothctl", "discoverable", "on"], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(["bluetoothctl", "discoverable", "off"], capture_output=True, text=True, timeout=5)
            return "succeeded" in result.stdout.lower()
        except:
            return False


if __name__ == "__main__":
    # Test the Bluetooth manager
    bt = BluetoothManager()

    print("Bluetooth powered:", bt.is_powered())

    if not bt.is_powered():
        print("Turning on Bluetooth...")
        bt.power_on()

    print("\nKnown devices:")
    for device in bt.get_devices():
        status = []
        if device.paired:
            status.append("paired")
        if device.connected:
            status.append("connected")
        if device.trusted:
            status.append("trusted")
        print(f"  {device.name} ({device.address}) - {', '.join(status) or 'not paired'}")

    print("\nScanning for devices (10 seconds)...")
    devices = bt.scan(duration=10)
    print(f"Found {len(devices)} devices")
    for d in devices:
        print(f"  {d.name} ({d.address})")
