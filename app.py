import streamlit as st
import os
import sys
import torch
import time
import numpy as np
import json
import shutil
from PIL import Image
from pathlib import Path

# Add project root to path
sys.path.append('.')

from training.config import get_config
from training.inference import Inference

# Page config
st.set_page_config(
    page_title="EleGANt Makeup Transfer",
    page_icon="💄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #FF6B9D 0%, #C06C84 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6B9D;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #C06C84;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">💄 EleGANt Makeup Transfer</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Transform your look with AI-powered makeup transfer</p>', unsafe_allow_html=True)

# Initialize session state
if 'model_loaded' not in st.session_state:
    st.session_state.model_loaded = False
    st.session_state.inference = None

# Load model
@st.cache_resource
def load_model():
    """Load the EleGANt model"""
    config = get_config()
    
    # Create args object
    class Args:
        def __init__(self):
            self.device = torch.device('cpu')
            self.gpu = 'cpu'
    
    args = Args()
    model_path = 'ckpts/sow_pyramid_a5_e3d2_remapped.pth'
    
    if not os.path.exists(model_path):
        st.error(f"Model checkpoint not found at {model_path}")
        return None
    
    inference = Inference(config, args, model_path)
    return inference

# Preset management functions
def get_presets_dir():
    """Get or create the presets directory"""
    presets_dir = Path('presets')
    presets_dir.mkdir(exist_ok=True)
    return presets_dir

def save_preset(preset_name, reference_image, config):
    """Save a preset with reference image and configuration"""
    presets_dir = get_presets_dir()
    preset_dir = presets_dir / preset_name
    preset_dir.mkdir(exist_ok=True)
    
    # Save reference image
    ref_path = preset_dir / 'reference.png'
    reference_image.save(str(ref_path))
    
    # Save configuration
    config_path = preset_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return True

def load_preset(preset_name):
    """Load a preset configuration and reference image"""
    presets_dir = get_presets_dir()
    preset_dir = presets_dir / preset_name
    
    if not preset_dir.exists():
        return None, None
    
    # Load reference image
    ref_path = preset_dir / 'reference.png'
    if not ref_path.exists():
        return None, None
    
    reference_image = Image.open(ref_path).convert('RGB')
    
    # Load configuration
    config_path = preset_dir / 'config.json'
    if not config_path.exists():
        return reference_image, {}
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return reference_image, config

def get_available_presets():
    """Get list of available presets"""
    presets_dir = get_presets_dir()
    if not presets_dir.exists():
        return []
    
    presets = []
    for item in presets_dir.iterdir():
        if item.is_dir() and (item / 'config.json').exists():
            presets.append(item.name)
    
    return sorted(presets)

def delete_preset(preset_name):
    """Delete a preset"""
    presets_dir = get_presets_dir()
    preset_dir = presets_dir / preset_name
    
    if preset_dir.exists():
        shutil.rmtree(preset_dir)
        return True
    return False

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("""
    **EleGANt** is an AI model for makeup transfer that can:
    - Transfer makeup from reference image to source image
    - Preserve facial features and identity
    - Generate natural-looking results
    
    **How to use:**
    1. Upload a source image (without makeup)
    2. Upload a reference image (with makeup)
    3. Click "Apply Makeup Transfer"
    4. Wait for processing and view results
    """)
    
    st.header("⚙️ Settings")
    st.markdown("---")
    st.subheader("🎨 Makeup Intensity")
    
    # Initialize preset reload counter if not exists
    if 'preset_reload_count' not in st.session_state:
        st.session_state.preset_reload_count = 0
    
    # Get default values from loaded preset or use defaults
    if 'loaded_preset_config' in st.session_state and st.session_state.loaded_preset_config:
        config = st.session_state.loaded_preset_config
        default_lip = config.get('lip_intensity', 1.0)
        default_skin = config.get('skin_intensity', 1.0)
        default_eye = config.get('eye_intensity', 1.0)
    else:
        default_lip = 1.0
        default_skin = 1.0
        default_eye = 1.0
    
    # Use dynamic keys to force slider update when preset changes
    slider_key_suffix = f"_{st.session_state.preset_reload_count}"
    
    lip_intensity = st.slider(
        "💄 Độ đậm son môi",
        min_value=0.0,
        max_value=1.5,
        value=default_lip,
        step=0.05,
        help="0.0 = không son, 1.0 = bình thường, 1.5 = đậm hơn",
        key=f"lip_slider{slider_key_suffix}"
    )
    skin_intensity = st.slider(
        "✨ Độ đậm makeup da",
        min_value=0.0,
        max_value=1.5,
        value=default_skin,
        step=0.05,
        help="Điều chỉnh foundation, blush và các makeup trên da",
        key=f"skin_slider{slider_key_suffix}"
    )
    eye_intensity = st.slider(
        "👁️ Độ đậm makeup mắt",
        min_value=0.0,
        max_value=1.5,
        value=default_eye,
        step=0.05,
        help="Điều chỉnh eyeshadow, eyeliner và các makeup mắt",
        key=f"eye_slider{slider_key_suffix}"
    )
    
    # Preset Management
    st.markdown("---")
    st.subheader("💾 Presets")
    
    # Load existing preset
    available_presets = get_available_presets()
    
    if available_presets:
        st.write("**Load Preset:**")
        selected_preset = st.selectbox(
            "Choose a preset",
            options=["-- None --"] + available_presets,
            key="preset_selector"
        )
        
        col_load, col_del = st.columns(2)
        
        with col_load:
            if st.button("📂 Load", width='stretch', disabled=(selected_preset == "-- None --")):
                if selected_preset != "-- None --":
                    ref_img, config = load_preset(selected_preset)
                    if ref_img and config:
                        st.session_state.loaded_preset_ref = ref_img
                        st.session_state.loaded_preset_config = config
                        st.session_state.loaded_preset_name = selected_preset
                        # Increment counter to force slider recreation with new values
                        st.session_state.preset_reload_count = st.session_state.get('preset_reload_count', 0) + 1
                        st.success(f"✅ Loaded preset: {selected_preset}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to load preset")
        
        with col_del:
            if st.button("🗑️ Delete", width='stretch', disabled=(selected_preset == "-- None --")):
                if selected_preset != "-- None --":
                    if delete_preset(selected_preset):
                        st.success(f"✅ Deleted: {selected_preset}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete preset")
    
    # Save new preset
    st.write("**Save Current Settings:**")
    with st.form("save_preset_form"):
        preset_name = st.text_input(
            "Preset name",
            placeholder="e.g., Natural Look, Evening Glam",
            help="Enter a name for this preset"
        )
        save_button = st.form_submit_button("💾 Save Preset", width='stretch')
        
        if save_button:
            if not preset_name:
                st.error("❌ Please enter a preset name")
            elif 'reference_file_for_preset' not in st.session_state or st.session_state.reference_file_for_preset is None:
                st.error("❌ Please upload a reference image first")
            else:
                # Save the preset
                config = {
                    "lip_intensity": lip_intensity,
                    "skin_intensity": skin_intensity,
                    "eye_intensity": eye_intensity
                }
                
                try:
                    save_preset(preset_name, st.session_state.reference_file_for_preset, config)
                    st.success(f"✅ Preset saved: {preset_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving preset: {str(e)}")

# Load model on first run
if not st.session_state.model_loaded:
    with st.spinner("Loading model... This may take a moment."):
        st.session_state.inference = load_model()
        if st.session_state.inference is not None:
            st.session_state.model_loaded = True
            st.success("✅ Model loaded successfully!")

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("📸 Source Images (No Makeup)")
    # Add option to choose between single or multiple files
    batch_mode = st.checkbox("🔢 Batch Mode (Multiple Files)", value=False, 
                             help="Enable to process multiple source images at once")
    
    if batch_mode:
        source_files = st.file_uploader(
            "Upload source images (up to 10 files)", 
            type=['png', 'jpg', 'jpeg'],
            key="source",
            accept_multiple_files=True
        )
        
        if source_files:
            st.info(f"📊 {len(source_files)} file(s) selected")
            # Show thumbnails
            cols = st.columns(min(4, len(source_files)))
            for idx, file in enumerate(source_files[:8]):  # Show max 8 previews
                with cols[idx % 4]:
                    img = Image.open(file).convert('RGB')
                    st.image(img, caption=f"Source {idx+1}", width='stretch')
    else:
        source_files = st.file_uploader(
            "Upload source image", 
            type=['png', 'jpg', 'jpeg'],
            key="source",
            accept_multiple_files=False
        )
        
        if source_files:
            source_img = Image.open(source_files).convert('RGB')
            st.image(source_img, caption="Source Image", width='stretch')
            source_files = [source_files]  # Convert to list for consistency

with col2:
    st.subheader("💅 Reference Image (With Makeup)")
    
    # Check if a preset was loaded
    if 'loaded_preset_ref' in st.session_state and st.session_state.loaded_preset_ref is not None:
        st.info(f"📋 Using preset: {st.session_state.get('loaded_preset_name', 'Unknown')}")
        reference_img = st.session_state.loaded_preset_ref
        st.image(reference_img, caption=f"Reference (from preset)", width='stretch')
        
        # Store for preset saving
        st.session_state.reference_file_for_preset = reference_img
        
        reference_file = None  # Mark that we're using preset
        
        if st.button("🔄 Clear Preset", width='stretch'):
            st.session_state.loaded_preset_ref = None
            st.session_state.loaded_preset_config = None
            st.session_state.loaded_preset_name = None
            # Increment counter to force slider recreation with default values
            st.session_state.preset_reload_count = st.session_state.get('preset_reload_count', 0) + 1
            st.rerun()
    else:
        reference_file = st.file_uploader(
            "Upload reference image",
            type=['png', 'jpg', 'jpeg'],
            key="reference"
        )
        
        if reference_file:
            reference_img = Image.open(reference_file).convert('RGB')
            st.image(reference_img, caption="Reference Image", width='stretch')
            
            # Store for preset saving
            st.session_state.reference_file_for_preset = reference_img

# Processing button
st.markdown("---")
process_button = st.button("✨ Apply Makeup Transfer", type="primary", width='stretch')

if process_button:
    if not st.session_state.model_loaded:
        st.error("❌ Model not loaded. Please refresh the page.")
    elif not source_files:
        st.warning("⚠️ Please upload source image(s)")
    elif not reference_file and ('loaded_preset_ref' not in st.session_state or st.session_state.loaded_preset_ref is None):
        st.warning("⚠️ Please upload a reference image or load a preset")
    else:
        # Get reference image
        if 'loaded_preset_ref' in st.session_state and st.session_state.loaded_preset_ref is not None:
            reference_img = st.session_state.loaded_preset_ref
        else:
            reference_img = Image.open(reference_file).convert('RGB')
        
        # Handle single vs multiple files
        if not isinstance(source_files, list):
            source_files = [source_files]
        
        num_files = len(source_files)
        
        # Process
        st.markdown("---")
        st.subheader(f"🔄 Processing {num_files} image(s)...")
        
        # Overall progress
        overall_progress = st.progress(0)
        overall_status = st.empty()
        
        # Results storage
        all_results = []
        processing_times = []
        failed_files = []
        
        # Process each file
        for idx, source_file in enumerate(source_files):
            try:
                source_img = Image.open(source_file).convert('RGB')
                file_name = source_file.name if hasattr(source_file, 'name') else f"Image {idx+1}"
                
                overall_status.text(f"Processing {idx+1}/{num_files}: {file_name}...")
                
                start_time = time.time()
                
                # Actual processing
                result_face, result_full = st.session_state.inference.transfer_with_intensity(
                    source_img, 
                    reference_img,
                    lip_intensity=lip_intensity,
                    skin_intensity=skin_intensity,
                    eye_intensity=eye_intensity,
                    postprocess=True,
                    return_full_image=True
                )
                
                elapsed_time = time.time() - start_time
                processing_times.append(elapsed_time)
                
                if result_face is None:
                    failed_files.append((idx, file_name, "No face detected"))
                else:
                    all_results.append({
                        'index': idx,
                        'name': file_name,
                        'source': source_img,
                        'result_face': result_face,
                        'result_full': result_full,
                        'time': elapsed_time
                    })
                
                # Update progress
                overall_progress.progress((idx + 1) / num_files)
                
            except Exception as e:
                failed_files.append((idx, file_name if hasattr(source_file, 'name') else f"Image {idx+1}", str(e)))
        
        # Calculate statistics
        total_time = sum(processing_times)
        avg_time = total_time / len(processing_times) if processing_times else 0
        
        overall_status.text(f"✅ Completed! Total: {total_time:.2f}s | Average: {avg_time:.2f}s per image")
        
        # Display statistics
        st.markdown("---")
        st.subheader("📊 Processing Statistics")
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("Total Images", num_files)
        with col_s2:
            st.metric("Successful", len(all_results), delta=None if len(all_results) == num_files else f"-{len(failed_files)}")
        with col_s3:
            st.metric("Total Time", f"{total_time:.2f}s")
        with col_s4:
            st.metric("Avg Time/Image", f"{avg_time:.2f}s")
        
        # Show failed files if any
        if failed_files:
            st.warning(f"⚠️ {len(failed_files)} file(s) failed to process:")
            for idx, name, error in failed_files:
                st.text(f"  • {name}: {error}")
        
        # Display results
        if all_results:
            st.markdown("---")
            st.subheader("✨ Results")
            
            # Display each result
            for result in all_results:
                with st.expander(f"📷 {result['name']} - {result['time']:.2f}s", expanded=(num_files <= 3)):
                    # Create comparison view - 4 columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.image(result['source'], caption="Source", width='stretch')
                    
                    with col2:
                        st.image(reference_img, caption="Reference", width='stretch')
                    
                    with col3:
                        st.image(result['result_face'], caption="Face Only", width='stretch')
                    
                    with col4:
                        st.image(result['result_full'], caption="Full Image", width='stretch')
                    
                    # Download buttons
                    from io import BytesIO
                    
                    buf_face = BytesIO()
                    result['result_face'].save(buf_face, format="PNG")
                    byte_face = buf_face.getvalue()
                    
                    buf_full = BytesIO()
                    result['result_full'].save(buf_full, format="PNG")
                    byte_full = buf_full.getvalue()
                    
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        st.download_button(
                            label="⬇️ Face Only",
                            data=byte_face,
                            file_name=f"makeup_{result['index']+1}_face.png",
                            mime="image/png",
                            key=f"dl_face_{result['index']}"
                        )
                    
                    with col_dl2:
                        st.download_button(
                            label="⬇️ Full Image",
                            data=byte_full,
                            file_name=f"makeup_{result['index']+1}_full.png",
                            mime="image/png",
                            key=f"dl_full_{result['index']}"
                        )
            
            # Batch download all results
            if len(all_results) > 1:
                st.markdown("---")
                st.subheader("📦 Batch Download")
                
                import zipfile
                from io import BytesIO
                
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for result in all_results:
                        # Add face-only result
                        buf_face = BytesIO()
                        result['result_face'].save(buf_face, format="PNG")
                        zip_file.writestr(f"face_only/makeup_{result['index']+1}_face.png", buf_face.getvalue())
                        
                        # Add full image result
                        buf_full = BytesIO()
                        result['result_full'].save(buf_full, format="PNG")
                        zip_file.writestr(f"full_image/makeup_{result['index']+1}_full.png", buf_full.getvalue())
                
                st.download_button(
                    label=f"⬇️ Download All ({len(all_results)} images as ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="makeup_transfer_batch.zip",
                    mime="application/zip",
                    type="primary",
                    width='stretch'
                )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Powered by EleGANt - ECCV 2022 | Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
