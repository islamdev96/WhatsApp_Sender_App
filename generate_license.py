"""WhatsApp Sender Pro — License Key Generator Utility.

Used by the administrator/reseller to generate activation keys for client HWIDs.
Usage: python generate_license.py <HWID>
"""
import sys
from utils.licensing import generate_license_key, get_hwid


def main():
    if len(sys.argv) < 2:
        print("\n==============================================")
        print("WhatsApp Sender Pro — License Key Generator")
        print("==============================================")
        print("Usage: python generate_license.py <CLIENT_HWID>")
        print("\nYour Local Machine's HWID is:")
        print(f"HWID: {get_hwid()}")
        print("Expected Key:")
        print(f"KEY : {generate_license_key(get_hwid())}")
        print("==============================================\n")
        return

    client_hwid = sys.argv[1].strip()
    key = generate_license_key(client_hwid)
    print("\n==============================================")
    print(f"Client HWID : {client_hwid}")
    print(f"Generated Key: {key}")
    print("==============================================\n")


if __name__ == "__main__":
    main()
