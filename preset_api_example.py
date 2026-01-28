"""
Example client demonstrating the use of presets with the EleGANt API

This script shows how to:
1. List available presets
2. Transfer makeup using a preset
3. Compare preset-based transfer with manual configuration
"""

import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def list_presets():
    """List all available presets"""
    print("\n" + "="*60)
    print("LISTING AVAILABLE PRESETS")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/presets")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nFound {data['count']} preset(s):\n")
        
        for preset in data['presets']:
            print(f"📋 {preset['name']}")
            print(f"   Path: {preset['path']}")
            if 'config' in preset:
                config = preset['config']
                print(f"   Config:")
                print(f"     - Lip: {config.get('lip_intensity', 'N/A')}")
                print(f"     - Skin: {config.get('skin_intensity', 'N/A')}")
                print(f"     - Eye: {config.get('eye_intensity', 'N/A')}")
            print()
        
        return data['presets']
    else:
        print(f"❌ Error: {response.status_code}")
        return []

def transfer_with_preset(source_images, preset_path, session_id, save_face_only=False):
    """
    Transfer makeup using a preset
    
    Args:
        source_images: List of paths to source images
        preset_path: Path to preset folder (e.g., "presets/Natural Look")
        session_id: Unique session ID
        save_face_only: Whether to save only face region
    """
    print("\n" + "="*60)
    print(f"TRANSFERRING WITH PRESET: {preset_path}")
    print("="*60)
    
    payload = {
        "source_images": source_images,
        "preset_path": preset_path,
        "session_id": session_id,
        "save_face_only": save_face_only
    }
    
    print(f"\n📤 Sending request...")
    print(f"   Source images: {len(source_images)}")
    print(f"   Session ID: {session_id}")
    print(f"   Save face only: {save_face_only}")
    
    response = requests.post(f"{BASE_URL}/transfer-preset", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ {result['message']}")
        print(f"\n📊 Statistics:")
        print(f"   Total images: {result['total_images']}")
        print(f"   Successful: {result['successful']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Processing time: {result['processing_time']}s")
        print(f"   Output folder: {result['output_folder']}")
        
        if result['results']:
            print(f"\n📸 Results:")
            for item in result['results']:
                print(f"   ✓ {item['output_filename']}")
                print(f"     Source: {item['source_path']}")
                print(f"     Output: {item['output_path']}")
                print(f"     Time: {item['processing_time']}s")
                if 'preset_used' in item:
                    print(f"     Preset: {item['preset_used']}")
                if 'config' in item:
                    cfg = item['config']
                    print(f"     Config: Lip={cfg['lip_intensity']}, Skin={cfg['skin_intensity']}, Eye={cfg['eye_intensity']}")
                print()
        
        if result.get('errors'):
            print(f"\n⚠️ Errors:")
            for error in result['errors']:
                print(f"   ✗ {error['path']}: {error['error']}")
        
        return result
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")
        return None

def transfer_manual(source_images, reference_image, session_id, 
                   lip_intensity=1.0, skin_intensity=1.0, eye_intensity=1.0,
                   save_face_only=False):
    """
    Transfer makeup with manual configuration (for comparison)
    
    Args:
        source_images: List of paths to source images
        reference_image: Path to reference image
        session_id: Unique session ID
        lip_intensity: Lip makeup intensity
        skin_intensity: Skin makeup intensity
        eye_intensity: Eye makeup intensity
        save_face_only: Whether to save only face region
    """
    print("\n" + "="*60)
    print("TRANSFERRING WITH MANUAL CONFIGURATION")
    print("="*60)
    
    payload = {
        "source_images": source_images,
        "reference_image": reference_image,
        "session_id": session_id,
        "lip_intensity": lip_intensity,
        "skin_intensity": skin_intensity,
        "eye_intensity": eye_intensity,
        "save_face_only": save_face_only
    }
    
    print(f"\n📤 Sending request...")
    print(f"   Source images: {len(source_images)}")
    print(f"   Reference: {reference_image}")
    print(f"   Config: Lip={lip_intensity}, Skin={skin_intensity}, Eye={eye_intensity}")
    
    response = requests.post(f"{BASE_URL}/transfer", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ {result['message']}")
        return result
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")
        return None

def check_health():
    """Check API health"""
    print("\n" + "="*60)
    print("CHECKING API HEALTH")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Status: {data['status']}")
        print(f"   Model loaded: {data['model_loaded']}")
        print(f"   Model path: {data['model_path']}")
        print(f"   Model exists: {data['model_exists']}")
    else:
        print(f"\n❌ Error: {response.status_code}")

# Example usage
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║      EleGANt Makeup Transfer - Preset API Examples          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if API is running
    try:
        check_health()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API. Make sure the server is running:")
        print("   python api.py")
        exit(1)
    
    # List available presets
    presets = list_presets()
    
    # Example 1: Transfer using preset (if presets are available)
    if presets:
        print("\n" + "="*60)
        print("EXAMPLE 1: Transfer using a preset")
        print("="*60)
        
        # Use the first available preset
        preset_to_use = presets[0]
        
        # Example source images (replace with your actual image paths)
        example_sources = [
            "path/to/your/source1.jpg",
            "path/to/your/source2.jpg"
        ]
        
        print(f"\n💡 To use this example, update the source image paths in the script")
        print(f"   Current paths: {example_sources}")
        print(f"\n   Then uncomment the following line to run the transfer:")
        print(f"   # transfer_with_preset(example_sources, '{preset_to_use['path']}', 'session_preset_001')")
        
        # Uncomment to run:
        # transfer_with_preset(example_sources, preset_to_use['path'], 'session_preset_001')
    else:
        print("\n⚠️ No presets found. Create a preset first using the Streamlit app.")
    
    # Example 2: Manual transfer for comparison
    print("\n" + "="*60)
    print("EXAMPLE 2: Manual transfer (for comparison)")
    print("="*60)
    
    example_sources = ["path/to/your/source.jpg"]
    example_reference = "path/to/your/reference.jpg"
    
    print(f"\n💡 To use this example, update the paths and uncomment:")
    print(f"   # transfer_manual(")
    print(f"   #     example_sources,")
    print(f"   #     example_reference,")
    print(f"   #     'session_manual_001',")
    print(f"   #     lip_intensity=1.2,")
    print(f"   #     skin_intensity=1.0,")
    print(f"   #     eye_intensity=1.1")
    print(f"   # )")
    
    # Uncomment to run:
    # transfer_manual(
    #     example_sources,
    #     example_reference,
    #     'session_manual_001',
    #     lip_intensity=1.2,
    #     skin_intensity=1.0,
    #     eye_intensity=1.1
    # )
    
    print("\n" + "="*60)
    print("For more information, see PRESET_README.md")
    print("="*60 + "\n")
