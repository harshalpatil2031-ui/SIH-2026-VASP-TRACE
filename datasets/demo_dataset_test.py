import json
import os

def test_dataset():
    filepath = os.path.join(os.path.dirname(__file__), "known_vasp_directory.json")
    with open(filepath, "r") as f:
        data = json.load(f)
    
    print(f"=== Ground Truth VASP Intelligence Dataset ===")
    print(f"Version: {data['version']}")
    print(f"Total VASPs Indexed: {len(data['vasps'])}\n")
    
    for v in data["vasps"]:
        print(f"🏢 {v['vasp_name']}")
        print(f"   Country: {v['country']} | FIU Registered: {v['fiu_ind_registered']} ({v['fiu_registration_number']})")
        print(f"   Chains: {', '.join(v['supported_chains'])}")
        print(f"   Indexed Hot Wallets: {len(v['known_hot_wallets'])}")
        print(f"   Sweep Window: ~{v['deposit_sweep_pattern']['sweep_time_window_minutes']} mins")
        print("-" * 50)

if __name__ == "__main__":
    test_dataset()
