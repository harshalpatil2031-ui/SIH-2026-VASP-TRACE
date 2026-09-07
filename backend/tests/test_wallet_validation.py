import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_sources.blockchain_ingestion import BlockchainIngestionAdapter
adapter = BlockchainIngestionAdapter()
def test_tron_valid():
    r = adapter.validate_wallet_address("TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6")
    assert r["valid"] == True; print("PASS: TRON valid")
def test_evm_valid():
    r = adapter.validate_wallet_address("0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C")
    assert r["valid"] == True; print("PASS: EVM valid")
def test_short_invalid():
    r = adapter.validate_wallet_address("1")
    assert r["valid"] == False; print("PASS: Short input rejected")
def test_empty_invalid():
    r = adapter.validate_wallet_address("")
    assert r["valid"] == False; print("PASS: Empty input rejected")
if __name__ == "__main__":
    test_tron_valid(); test_evm_valid(); test_short_invalid(); test_empty_invalid()
    print("\nAll 4 tests passed!")
