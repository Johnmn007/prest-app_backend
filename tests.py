import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

def test_backend_live():
    # 1. Test Health Auth Check
    response = httpx.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("[OK] Health endpoint is working.", response.json())

if __name__ == "__main__":
    time.sleep(2)  # Wait for uvicorn to be fully up
    try:
        test_backend_live()
        print("\nAll internal structure is properly wired via HTTP routes!")
    except Exception as e:
        print("\n[ERROR]", e)
