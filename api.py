from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import torch
import time
import shutil
import json
from PIL import Image
from pathlib import Path

# Add project root to path
sys.path.append('.')

from training.config import get_config
from training.inference import Inference

app = FastAPI(
    title="EleGANt Makeup Transfer API",
    description="API for AI-powered makeup transfer",
    version="1.0.0"
)

# Global model instance
model_instance = None

class MakeupRequest(BaseModel):
    source_images: List[str]  # Danh sách đường dẫn ảnh source
    reference_image: str  # Đường dẫn ảnh reference
    session_id: str  # Session ID để tạo folder riêng cho mỗi session
    output_folder: Optional[str] = "result"  # Folder gốc lưu kết quả
    lip_intensity: Optional[float] = 1.0
    skin_intensity: Optional[float] = 1.0
    eye_intensity: Optional[float] = 1.0
    save_face_only: Optional[bool] = False  # True: chỉ lưu face, False: lưu full image

class PresetTransferRequest(BaseModel):
    source_images: List[str]  # List of paths to source images
    preset_path: str  # Path to preset folder (e.g., "presets/Natural Look")
    session_id: str  # Session ID for output organization
    output_folder: Optional[str] = "result"  # Base output folder
    save_face_only: Optional[bool] = False  # True: save only face, False: save full image

class MakeupResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    output_folder: str
    total_images: int
    successful: int
    failed: int
    processing_time: float
    results: List[dict]
    errors: Optional[List[dict]] = None

def load_model():
    """Load the EleGANt model"""
    global model_instance
    
    if model_instance is not None:
        return model_instance
    
    config = get_config()
    
    # Create args object
    class Args:
        def __init__(self):
            self.device = torch.device('cpu')
            self.gpu = 'cpu'
    
    args = Args()
    model_path = 'ckpts/sow_pyramid_a5_e3d2_remapped.pth'
    
    if not os.path.exists(model_path):
        raise Exception(f"Model checkpoint not found at {model_path}")
    
    model_instance = Inference(config, args, model_path)
    return model_instance

def load_preset_config(preset_path):
    """Load preset configuration and reference image from preset folder"""
    preset_dir = Path(preset_path)
    
    if not preset_dir.exists() or not preset_dir.is_dir():
        raise ValueError(f"Preset folder not found: {preset_path}")
    
    # Load reference image
    ref_path = preset_dir / 'reference.png'
    if not ref_path.exists():
        raise ValueError(f"Reference image not found in preset: {ref_path}")
    
    reference_img = Image.open(ref_path).convert('RGB')
    
    # Load configuration
    config_path = preset_dir / 'config.json'
    if not config_path.exists():
        raise ValueError(f"Configuration file not found in preset: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return reference_img, config

@app.on_event("startup")
async def startup_event():
    """Load model when server starts"""
    print("Loading EleGANt model...")
    try:
        load_model()
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {str(e)}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "EleGANt Makeup Transfer API",
        "model_loaded": model_instance is not None
    }

@app.post("/transfer", response_model=MakeupResponse)
async def transfer_makeup(request: MakeupRequest):
    """
    Transfer makeup from reference image to source images
    
    Parameters:
    - source_images: List of paths to source images (without makeup)
    - reference_image: Path to reference image (with makeup)
    - session_id: Session ID to create separate folder for this session (required)
    - output_folder: Base output folder (default: "result")
    - lip_intensity: Lip makeup intensity (0.0 - 1.5, default: 1.0)
    - skin_intensity: Skin makeup intensity (0.0 - 1.5, default: 1.0)
    - eye_intensity: Eye makeup intensity (0.0 - 1.5, default: 1.0)
    - save_face_only: If True, save only face region; if False, save full image (default: False)
    """
    
    if model_instance is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Validate reference image
    if not os.path.exists(request.reference_image):
        raise HTTPException(status_code=404, detail=f"Reference image not found: {request.reference_image}")
    
    # Create output folder based on session_id
    output_folder = Path(request.output_folder) / request.session_id
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Load reference image
    try:
        reference_img = Image.open(request.reference_image).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading reference image: {str(e)}")
    
    # Process each source image
    results = []
    errors = []
    start_time = time.time()
    
    for idx, source_path in enumerate(request.source_images):
        try:
            # Validate source image exists
            if not os.path.exists(source_path):
                errors.append({
                    "index": idx,
                    "path": source_path,
                    "error": "File not found"
                })
                continue
            
            # Load source image
            source_img = Image.open(source_path).convert('RGB')
            
            # Get filename without extension
            source_file = Path(source_path)
            base_name = source_file.stem
            extension = source_file.suffix
            
            # Process image
            img_start = time.time()
            result_face, result_full = model_instance.transfer_all_faces(
                source_img,
                reference_img,
                postprocess=True,
                return_full_image=True
            )
            img_time = time.time() - img_start
            
            if result_face is None:
                errors.append({
                    "index": idx,
                    "path": source_path,
                    "error": "No face detected in source image"
                })
                continue
            
            # Save result
            output_filename = f"{base_name}_maked{extension}"
            output_path = output_folder / output_filename
            
            # Save face-only or full image based on parameter
            if request.save_face_only:
                result_face.save(str(output_path))
                result_type = "face_only"
            else:
                result_full.save(str(output_path))
                result_type = "full_image"
            
            results.append({
                "index": idx,
                "source_path": source_path,
                "output_path": str(output_path),
                "output_filename": output_filename,
                "result_type": result_type,
                "processing_time": round(img_time, 2)
            })
            
        except Exception as e:
            errors.append({
                "index": idx,
                "path": source_path,
                "error": str(e)
            })
    
    total_time = time.time() - start_time
    
    return MakeupResponse(
        success=len(results) > 0,
        message=f"Processed {len(results)} out of {len(request.source_images)} images successfully",
        session_id=request.session_id,
        output_folder=str(output_folder),
        total_images=len(request.source_images),
        successful=len(results),
        failed=len(errors),
        processing_time=round(total_time, 2),
        results=results,
        errors=errors if errors else None
    )

@app.post("/transfer-preset", response_model=MakeupResponse)
async def transfer_makeup_preset(request: PresetTransferRequest):
    """
    Transfer makeup using a preset configuration
    
    Parameters:
    - source_images: List of paths to source images (without makeup)
    - preset_path: Path to preset folder containing reference image and config.json
    - session_id: Session ID to create separate folder for this session (required)
    - output_folder: Base output folder (default: "result")
    - save_face_only: If True, save only face region; if False, save full image (default: False)
    
    The preset folder should contain:
    - reference.png: Reference image with makeup
    - config.json: Configuration with lip_intensity, skin_intensity, eye_intensity
    """
    
    if model_instance is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Load preset configuration and reference image
    try:
        reference_img, config = load_preset_config(request.preset_path)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading preset: {str(e)}")
    
    # Extract intensity values from config
    lip_intensity = config.get('lip_intensity', 1.0)
    skin_intensity = config.get('skin_intensity', 1.0)
    eye_intensity = config.get('eye_intensity', 1.0)
    
    # Create output folder based on session_id
    output_folder = Path(request.output_folder) / request.session_id
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Process each source image
    results = []
    errors = []
    start_time = time.time()
    
    for idx, source_path in enumerate(request.source_images):
        try:
            # Validate source image exists
            if not os.path.exists(source_path):
                errors.append({
                    "index": idx,
                    "path": source_path,
                    "error": "File not found"
                })
                continue
            
            # Load source image
            source_img = Image.open(source_path).convert('RGB')
            
            # Get filename without extension
            source_file = Path(source_path)
            base_name = source_file.stem
            extension = source_file.suffix
            
            # Process image
            img_start = time.time()
            result_face, result_full = model_instance.transfer_all_faces(
                source_img,
                reference_img,
                postprocess=True,
                return_full_image=True
            )
            img_time = time.time() - img_start
            
            if result_face is None:
                errors.append({
                    "index": idx,
                    "path": source_path,
                    "error": "No face detected in source image"
                })
                continue
            
            # Save result
            output_filename = f"{base_name}_maked{extension}"
            output_path = output_folder / output_filename
            
            # Save face-only or full image based on parameter
            if request.save_face_only:
                result_face.save(str(output_path))
                result_type = "face_only"
            else:
                result_full.save(str(output_path))
                result_type = "full_image"
            
            results.append({
                "index": idx,
                "source_path": source_path,
                "output_path": str(output_path),
                "output_filename": output_filename,
                "result_type": result_type,
                "processing_time": round(img_time, 2),
                "preset_used": request.preset_path,
                "config": {
                    "lip_intensity": lip_intensity,
                    "skin_intensity": skin_intensity,
                    "eye_intensity": eye_intensity
                }
            })
            
        except Exception as e:
            errors.append({
                "index": idx,
                "path": source_path,
                "error": str(e)
            })
    
    total_time = time.time() - start_time
    
    return MakeupResponse(
        success=len(results) > 0,
        message=f"Processed {len(results)} out of {len(request.source_images)} images successfully using preset: {request.preset_path}",
        session_id=request.session_id,
        output_folder=str(output_folder),
        total_images=len(request.source_images),
        successful=len(results),
        failed=len(errors),
        processing_time=round(total_time, 2),
        results=results,
        errors=errors if errors else None
    )

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": model_instance is not None,
        "model_path": "ckpts/sow_pyramid_a5_e3d2_remapped.pth",
        "model_exists": os.path.exists("ckpts/sow_pyramid_a5_e3d2_remapped.pth")
    }

@app.get("/presets")
async def list_presets():
    """
    List all available presets
    
    Returns a list of preset names that can be used with /transfer-preset
    """
    presets_dir = Path('presets')
    
    if not presets_dir.exists():
        return {
            "presets": [],
            "count": 0,
            "message": "No presets directory found"
        }
    
    presets = []
    for item in presets_dir.iterdir():
        if item.is_dir():
            config_path = item / 'config.json'
            ref_path = item / 'reference.png'
            
            if config_path.exists() and ref_path.exists():
                # Load config to get details
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    presets.append({
                        "name": item.name,
                        "path": str(item),
                        "config": config
                    })
                except:
                    # If config can't be loaded, just add the name
                    presets.append({
                        "name": item.name,
                        "path": str(item)
                    })
    
    return {
        "presets": sorted(presets, key=lambda x: x['name']),
        "count": len(presets)
    }

@app.get("/delete/{session_id}")
async def delete_session(session_id: str, output_folder: str = "result"):
    """
    Delete a session folder and all its contents
    
    Parameters:
    - session_id: The session ID to delete
    - output_folder: Base output folder (default: "result")
    """
    folder_path = Path(output_folder) / session_id
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail=f"Session folder not found: {session_id}")
    
    try:
        # Delete the entire session folder
        shutil.rmtree(folder_path)
        return {
            "success": True,
            "message": f"Session folder deleted successfully",
            "session_id": session_id,
            "deleted_path": str(folder_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session folder: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting EleGANt Makeup Transfer API Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
