#!/usr/bin/env python3
"""
Quality comparison script for EleGANt optimization validation.

Usage:
    python scripts/quality_check.py --baseline results/baseline/ --optimized results/optimized/
"""
import os
import sys
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from skimage.metrics import structural_similarity as ssim
    from skimage.metrics import peak_signal_noise_ratio as psnr
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False
    print("Warning: scikit-image not installed. Install with: pip install scikit-image")


def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    if not HAS_SKIMAGE:
        return 0.0
    
    if img1.shape != img2.shape:
        img2_pil = Image.fromarray(img2)
        img2_pil = img2_pil.resize((img1.shape[1], img1.shape[0]))
        img2 = np.array(img2_pil)
    
    if len(img1.shape) == 3:
        return ssim(img1, img2, channel_axis=2, data_range=255)
    return ssim(img1, img2, data_range=255)


def calculate_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    if not HAS_SKIMAGE:
        return 0.0
    
    if img1.shape != img2.shape:
        img2_pil = Image.fromarray(img2)
        img2_pil = img2_pil.resize((img1.shape[1], img1.shape[0]))
        img2 = np.array(img2_pil)
    
    return psnr(img1, img2, data_range=255)


def find_matching_images(baseline_dir: str, optimized_dir: str):
    baseline_path = Path(baseline_dir)
    optimized_path = Path(optimized_dir)
    
    image_extensions = {'.png', '.jpg', '.jpeg'}
    
    baseline_files = {f.name: f for f in baseline_path.iterdir() 
                      if f.suffix.lower() in image_extensions}
    optimized_files = {f.name: f for f in optimized_path.iterdir() 
                       if f.suffix.lower() in image_extensions}
    
    common = set(baseline_files.keys()) & set(optimized_files.keys())
    
    pairs = []
    for name in sorted(common):
        pairs.append({
            'name': name,
            'baseline': str(baseline_files[name]),
            'optimized': str(optimized_files[name])
        })
    
    return pairs


def compare_images(baseline_path: str, optimized_path: str):
    img1 = np.array(Image.open(baseline_path).convert('RGB'))
    img2 = np.array(Image.open(optimized_path).convert('RGB'))
    
    return {
        'ssim': calculate_ssim(img1, img2),
        'psnr': calculate_psnr(img1, img2)
    }


def run_quality_check(baseline_dir: str, optimized_dir: str):
    pairs = find_matching_images(baseline_dir, optimized_dir)
    
    if not pairs:
        return {
            'error': 'No matching images found',
            'baseline_dir': baseline_dir,
            'optimized_dir': optimized_dir
        }
    
    results = []
    ssim_values = []
    psnr_values = []
    
    for pair in pairs:
        metrics = compare_images(pair['baseline'], pair['optimized'])
        
        results.append({
            'image': pair['name'],
            'ssim': metrics['ssim'],
            'psnr': metrics['psnr']
        })
        
        ssim_values.append(metrics['ssim'])
        psnr_values.append(metrics['psnr'])
    
    return {
        'total_images': len(pairs),
        'ssim_mean': float(np.mean(ssim_values)),
        'ssim_min': float(np.min(ssim_values)),
        'ssim_max': float(np.max(ssim_values)),
        'ssim_std': float(np.std(ssim_values)),
        'psnr_mean': float(np.mean(psnr_values)),
        'psnr_min': float(np.min(psnr_values)),
        'psnr_max': float(np.max(psnr_values)),
        'psnr_std': float(np.std(psnr_values)),
        'per_image_results': results,
        'quality_passed': float(np.mean(ssim_values)) > 0.95
    }


def main():
    parser = argparse.ArgumentParser(
        description='Compare quality between baseline and optimized EleGANt results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/quality_check.py --baseline results/baseline/ --optimized results/after_caching/
    python scripts/quality_check.py --baseline results/baseline/ --optimized results/final/ --json report.json
        """
    )
    
    parser.add_argument('--baseline', type=str, required=True,
                        help='Directory with baseline output images')
    parser.add_argument('--optimized', type=str, required=True,
                        help='Directory with optimized output images')
    parser.add_argument('--json', type=str, default=None,
                        help='Path to save comparison as JSON')
    parser.add_argument('--threshold', type=float, default=0.95,
                        help='SSIM threshold for quality pass (default: 0.95)')
    
    args = parser.parse_args()
    
    if not HAS_SKIMAGE:
        print("ERROR: scikit-image is required for quality comparison")
        print("Install with: pip install scikit-image")
        sys.exit(1)
    
    print(f"Quality Check Configuration:")
    print(f"  Baseline: {args.baseline}")
    print(f"  Optimized: {args.optimized}")
    print(f"  SSIM threshold: {args.threshold}")
    print()
    
    results = run_quality_check(args.baseline, args.optimized)
    
    if 'error' in results:
        print(f"ERROR: {results['error']}")
        sys.exit(1)
    
    print("=" * 50)
    print("QUALITY CHECK RESULTS")
    print("=" * 50)
    print(f"Images compared: {results['total_images']}")
    print()
    print("SSIM (Structural Similarity):")
    print(f"  Mean: {results['ssim_mean']:.4f}")
    print(f"  Min:  {results['ssim_min']:.4f}")
    print(f"  Max:  {results['ssim_max']:.4f}")
    print(f"  Std:  {results['ssim_std']:.4f}")
    print()
    print("PSNR (Peak Signal-to-Noise Ratio):")
    print(f"  Mean: {results['psnr_mean']:.2f} dB")
    print(f"  Min:  {results['psnr_min']:.2f} dB")
    print(f"  Max:  {results['psnr_max']:.2f} dB")
    print(f"  Std:  {results['psnr_std']:.2f} dB")
    print()
    
    print("Per-image breakdown:")
    for r in results['per_image_results']:
        status = "PASS" if r['ssim'] >= args.threshold else "FAIL"
        print(f"  {r['image']}: SSIM={r['ssim']:.4f}, PSNR={r['psnr']:.2f} dB [{status}]")
    print()
    
    passed = results['ssim_mean'] >= args.threshold
    results['quality_passed'] = passed
    
    if passed:
        print(f"QUALITY CHECK: PASSED (SSIM {results['ssim_mean']:.4f} >= {args.threshold})")
    else:
        print(f"QUALITY CHECK: FAILED (SSIM {results['ssim_mean']:.4f} < {args.threshold})")
    
    if args.json:
        os.makedirs(os.path.dirname(args.json) or '.', exist_ok=True)
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.json}")
    
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
