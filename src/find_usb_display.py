import subprocess
import json

def find_usb_devices_windows():
    try:
        # Get USB devices using PowerShell
        cmd = """
        Get-WmiObject -Class Win32_USBControllerDevice | 
        ForEach-Object { [wmi]($_.Dependent) } | 
        Where-Object { $_.Name -match "display|monitor|screen|lcd" -or $_.DeviceID -match "VID_|PID_" } |
        Select-Object Name, DeviceID, Manufacturer, Service |
        ConvertTo-Json -Depth 2
        """
        
        result = subprocess.run(['powershell', '-Command', cmd], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout.strip():
            devices = json.loads(result.stdout)
            if not isinstance(devices, list):
                devices = [devices]
                
            for device in devices:
                print(f"Name: {device.get('Name', 'Unknown')}")
                print(f"DeviceID: {device.get('DeviceID', 'Unknown')}")
                print(f"Manufacturer: {device.get('Manufacturer', 'Unknown')}")
                print("---")
        else:
            print("No USB display devices found")
            
    except Exception as e:
        print(f"Error: {e}")

def get_all_usb_devices():
    try:
        # Get ALL USB devices to find your display
        cmd = "Get-WmiObject -Class Win32_PnPEntity | Where-Object { $_.DeviceID -like '*USB*' } | Select-Object Name, DeviceID | ConvertTo-Json"
        
        result = subprocess.run(['powershell', '-Command', cmd], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout.strip():
            devices = json.loads(result.stdout)
            if not isinstance(devices, list):
                devices = [devices]
                
            print("ALL USB DEVICES:")
            for device in devices:
                name = device.get('Name', 'Unknown')
                device_id = device.get('DeviceID', 'Unknown')
                print(f"{name} | {device_id}")
                
    except Exception as e:
        print(f"Error: {e}")

# Run both
print("=== LOOKING FOR DISPLAY DEVICES ===")
find_usb_devices_windows()

print("\n=== ALL USB DEVICES ===")
get_all_usb_devices()