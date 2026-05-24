import subprocess

def main():
    target_path = r"E:\WhatsApp_Sender_App\data\profiles\Default"
    print(f"[KILL-LOCK] Searching for chrome.exe instances locked on: {target_path}")
    try:
        output = subprocess.check_output(["wmic", "process", "where", "name='chrome.exe'", "get", "CommandLine,ProcessId"]).decode("utf-8", errors="ignore")
        count = 0
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            if target_path.lower() in line.lower():
                parts = line.split()
                pid = parts[-1]
                print(f"[KILL-LOCK] Found locked chrome process PID: {pid}. Terminating...")
                subprocess.run(["taskkill", "/F", "/PID", pid])
                count += 1
        if count == 0:
            print("[KILL-LOCK] No locked chrome.exe processes found.")
        else:
            print(f"[KILL-LOCK] Successfully terminated {count} locked chrome.exe processes.")
    except Exception as e:
        print(f"[KILL-LOCK] Error searching/killing: {e}")

if __name__ == "__main__":
    main()
