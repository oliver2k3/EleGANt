import streamlit as st
import os
import sys
import torch
import time
import numpy as np
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
    
    lip_intensity = st.slider(
        "💄 Độ đậm son môi",
        min_value=0.0,
        max_value=1.5,
        value=1.0,
        step=0.05,
        help="0.0 = không son, 1.0 = bình thường, 1.5 = đậm hơn"
    )
    skin_intensity = st.slider(
        "✨ Độ đậm makeup da",
        min_value=0.0,
        max_value=1.5,
        value=1.0,
        step=0.05,
        help="Điều chỉnh foundation, blush và các makeup trên da"
    )
    eye_intensity = st.slider(
        "👁️ Độ đậm makeup mắt",
        min_value=0.0,
        max_value=1.5,
        value=1.0,
        step=0.05,
        help="Điều chỉnh eyeshadow, eyeliner và các makeup mắt"
    )

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
    st.subheader("📸 Source Image (No Makeup)")
    source_file = st.file_uploader(
        "Upload source image", 
        type=['png', 'jpg', 'jpeg'],
        key="source"
    )
    
    if source_file:
        source_img = Image.open(source_file).convert('RGB')
        st.image(source_img, caption="Source Image", use_container_width=True)

with col2:
    st.subheader("💅 Reference Image (With Makeup)")
    reference_file = st.file_uploader(
        "Upload reference image",
        type=['png', 'jpg', 'jpeg'],
        key="reference"
    )
    
    if reference_file:
        reference_img = Image.open(reference_file).convert('RGB')
        st.image(reference_img, caption="Reference Image", use_container_width=True)

# Processing button
st.markdown("---")
process_button = st.button("✨ Apply Makeup Transfer", type="primary", use_container_width=True)

if process_button:
    if not st.session_state.model_loaded:
        st.error("❌ Model not loaded. Please refresh the page.")
    elif not source_file:
        st.warning("⚠️ Please upload a source image")
    elif not reference_file:
        st.warning("⚠️ Please upload a reference image")
    else:
        # Get images
        source_img = Image.open(source_file).convert('RGB')
        reference_img = Image.open(reference_file).convert('RGB')
        
        # Process
        st.markdown("---")
        st.subheader("🔄 Processing...")
        
        # Progress bar and timer
        progress_bar = st.progress(0)
        status_text = st.empty()
        timer_text = st.empty()
        
        start_time = time.time()
        
        # Simulate progress (actual processing happens in one go)
        progress_bar.progress(10)
        status_text.text("Detecting faces...")
        time.sleep(0.1)
        
        progress_bar.progress(30)
        status_text.text("Extracting features...")
        time.sleep(0.1)
        
        progress_bar.progress(50)
        status_text.text("Transferring makeup...")
        
        # Actual processing
        try:
            # Get both face-only result and full image result
            result_face, result_full = st.session_state.inference.transfer_with_intensity(
                source_img, 
                reference_img,
                lip_intensity=lip_intensity,
                skin_intensity=skin_intensity,
                eye_intensity=eye_intensity,
                postprocess=True,
                return_full_image=True
            )
            
            progress_bar.progress(80)
            status_text.text("Post-processing...")
            time.sleep(0.1)
            
            if result_face is None:
                st.error("❌ Processing failed. Please make sure both images contain clear faces.")
            else:
                progress_bar.progress(100)
                elapsed_time = time.time() - start_time
                status_text.text(f"✅ Completed in {elapsed_time:.2f} seconds")
                
                # Display results
                st.markdown("---")
                st.subheader("✨ Results - Comparison View")
                
                # Create comparison view - 4 columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.image(source_img, caption="Source (Before)", use_container_width=True)
                
                with col2:
                    st.image(reference_img, caption="Reference", use_container_width=True)
                
                with col3:
                    st.image(result_face, caption="Result - Face Only", use_container_width=True)
                
                with col4:
                    st.image(result_full, caption="Result - Full Image", use_container_width=True)
                
                # Side by side comparison for full images
                st.markdown("---")
                st.subheader("📊 Before & After - Full Image")
                col_before, col_after = st.columns(2)
                
                with col_before:
                    st.image(source_img, caption="Before", use_container_width=True)
                
                with col_after:
                    st.image(result_full, caption="After (with background)", use_container_width=True)
                
                # Download buttons
                st.markdown("---")
                
                from io import BytesIO
                
                # Download face-only result
                buf_face = BytesIO()
                result_face.save(buf_face, format="PNG")
                byte_face = buf_face.getvalue()
                
                # Download full image result
                buf_full = BytesIO()
                result_full.save(buf_full, format="PNG")
                byte_full = buf_full.getvalue()
                
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    st.download_button(
                        label="⬇️ Download Face Only",
                        data=byte_face,
                        file_name="makeup_transfer_face.png",
                        mime="image/png",
                        use_container_width=True
                    )
                
                with col_dl2:
                    st.download_button(
                        label="⬇️ Download Full Image (Recommended)",
                        data=byte_full,
                        file_name="makeup_transfer_full.png",
                        mime="image/png",
                        use_container_width=True,
                        type="primary"
                    )
                
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("")
            st.error(f"❌ Error during processing: {str(e)}")
            st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Powered by EleGANt - ECCV 2022 | Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
