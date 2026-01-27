import os
import sys
import argparse
import numpy as np
import cv2
import torch
from PIL import Image
sys.path.append('.')

from training.config import get_config
from training.inference import Inference
from training.utils import create_logger, print_args

def main(config, args):
    logger = create_logger(args.save_folder, args.name, 'info', console=True)
    print_args(args, logger)
    logger.info(config)

    inference = Inference(config, args, args.load_path)

    # If specific files are provided, use them; otherwise process all files in directories
    if args.source_file and args.reference_file:
        # Single file mode
        pairs = [(args.source_file, args.reference_file)]
        logger.info(f"Processing single pair: {args.source_file} + {args.reference_file}")
    else:
        # Directory mode (original behavior)
        n_imgname = sorted(os.listdir(args.source_dir))
        m_imgname = sorted(os.listdir(args.reference_dir))
        pairs = [(os.path.join(args.source_dir, n), os.path.join(args.reference_dir, m)) 
                 for n, m in zip(n_imgname, m_imgname)]
        logger.info(f"Processing {len(pairs)} image pairs from directories")
    
    for i, (source_path, reference_path) in enumerate(pairs):
        imgA = Image.open(source_path).convert('RGB')
        imgB = Image.open(reference_path).convert('RGB')

        # Get both face-only and full image results
        result_face, result_full = inference.transfer(imgA, imgB, postprocess=True, return_full_image=True) 
        if result_face is None:
            logger.warning(f"Skipping pair {i}: transfer failed")
            continue
        
        # Convert to numpy arrays
        imgA_np = np.array(imgA)
        imgB_np = np.array(imgB)
        
        # Get dimensions from source image
        h, w, _ = imgA_np.shape
        
        # Resize results and reference to match source dimensions for visualization
        result_face_resized = result_face.resize((w, h))
        result_full_resized = result_full.resize((w, h))
        imgB_resized = imgB.resize((w, h))
        
        result_face_np = np.array(result_face_resized)
        result_full_np = np.array(result_full_resized)
        imgB_resized_np = np.array(imgB_resized)
        
        # Stack images horizontally: source | reference | face result | full result
        vis_image = np.hstack((imgA_np, imgB_resized_np, result_face_np, result_full_np))
        
        # Generate output filenames
        if args.source_file:
            base_name = os.path.splitext(os.path.basename(args.source_file))[0]
            output_comparison = f"result_{base_name}_comparison.png"
            output_full = f"result_{base_name}_full.png"
        else:
            output_comparison = f"result_{i}_comparison.png"
            output_full = f"result_{i}_full.png"
        
        # Save comparison image
        save_path_comparison = os.path.join(args.save_folder, output_comparison)
        Image.fromarray(vis_image.astype(np.uint8)).save(save_path_comparison)
        logger.info(f"Saved comparison to {save_path_comparison}")
        
        # Save full image result separately
        save_path_full = os.path.join(args.save_folder, output_full)
        result_full.save(save_path_full)
        logger.info(f"Saved full image result to {save_path_full}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("argument for training")
    parser.add_argument("--name", type=str, default='demo')
    parser.add_argument("--save_path", type=str, default='result', help="path to save model")
    parser.add_argument("--load_path", type=str, help="folder to load model", 
                        default='ckpts/sow_pyramid_a5_e3d2_remapped.pth')

    parser.add_argument("--source-dir", type=str, default="assets/images/non-makeup",
                        help="Directory containing source images (without makeup)")
    parser.add_argument("--reference-dir", type=str, default="assets/images/makeup",
                        help="Directory containing reference images (with makeup)")
    parser.add_argument("--source-file", type=str, default=None,
                        help="Specific source image file path (overrides source-dir)")
    parser.add_argument("--reference-file", type=str, default=None,
                        help="Specific reference image file path (overrides reference-dir)")
    parser.add_argument("--gpu", default='0', type=str, help="GPU id to use or 'cpu'")

    args = parser.parse_args()
    
    # Validate arguments
    if args.source_file and not args.reference_file:
        parser.error("--source-file requires --reference-file")
    if args.reference_file and not args.source_file:
        parser.error("--reference-file requires --source-file")
    
    if args.gpu.lower() == 'cpu':
        args.gpu = 'cpu'
    else:
        args.gpu = 'cuda:' + args.gpu
    args.device = torch.device(args.gpu)

    args.save_folder = os.path.join(args.save_path, args.name)
    if not os.path.exists(args.save_folder):
        os.makedirs(args.save_folder)
    
    config = get_config()
    main(config, args)