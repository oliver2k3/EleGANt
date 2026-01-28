"""
Example usage of the EleGANt Makeup Transfer API
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/transfer"

# Example 1: Process single image
def example_single_image():
    payload = {
        "source_images": [
            "assets/images/non-makeup/vFG112.png"
        ],
        "reference_image": "assets/images/makeup/XMY-006.png",
        "session_id": "session_001",
        "output_folder": "result",
        "lip_intensity": 1.0,
        "skin_intensity": 1.0,
        "eye_intensity": 1.0,
        "save_face_only": False
    }
    
    response = requests.post(API_URL, json=payload)
    print("Single Image Example:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n" + "="*80 + "\n")

# Example 2: Process multiple images (batch)
def example_batch_processing():
    payload = {
        "source_images": [
            "assets/images/non-makeup/vFG112.png",
            "assets/images/non-makeup/vFG456.png",
            "assets/images/non-makeup/vFG789.png"
        ],
        "reference_image": "assets/images/makeup/XMY-006.png",
        "session_id": "session_batch_001",
        "output_folder": "result",
        "lip_intensity": 1.2,
        "skin_intensity": 0.8,
        "eye_intensity": 1.0,
        "save_face_only": False
    }
    
    response = requests.post(API_URL, json=payload)
    print("Batch Processing Example:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n" + "="*80 + "\n")

# Example 3: Custom intensity settings
def example_custom_intensity():
    payload = {
        "source_images": [
            "assets/images/non-makeup/vFG112.png"
        ],
        "reference_image": "assets/images/makeup/XMY-006.png",
        "session_id": "session_custom_001",
        "output_folder": "result",
        "lip_intensity": 1.5,  # Đậm hơn
        "skin_intensity": 0.5,  # Nhạt hơn
        "eye_intensity": 1.3,
        "save_face_only": True  # Chỉ lưu phần face
    }
    
    response = requests.post(API_URL, json=payload)
    print("Custom Intensity Example:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n" + "="*80 + "\n")

# Example 4: Delete session folder
def example_delete_session(session_id: str):
    response = requests.get(f"http://localhost:8000/delete/{session_id}")
    print(f"Delete Session '{session_id}':")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n" + "="*80 + "\n")

# Health check
def check_health():
    response = requests.get("http://localhost:8000/health")
    print("Health Check:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print("🔍 Checking API health...")
    check_health()
    
    print("📸 Running examples...")
    
    # Uncomment the examples you want to run:
    # example_single_image()
    # example_batch_processing()
    # example_custom_intensity()
    
    # Delete session after processing (use session_id from previous request)
    # example_delete_session("session_001")
