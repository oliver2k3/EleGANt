#!/usr/bin/env python3
"""
Benchmark script for EleGANt makeup transfer performance measurement.

Usage:
    python scripts/benchmark.py --images 8 --reference test_data/benchmark/reference.png
"""
import os
import sys
import argparse
import json
import time
import tracemalloc

sys.path.append('.')

import torch
from PIL import Image

from training.config import get_config
from training.inference import Inference


def create_args(device='cpu', model_path='ckpts/sow_pyramid_a5_e3d2_remapped.pth'):
    args = argparse.Namespace()
    args.device = torch.device(device)
    args.save_folder = 'result/benchmark'
    args.name = 'benchmark'
    return args, model_path


def load_images_from_manifest(manifest_path: str, max_images: int = None):
    manifest_dir = os.path.dirname(manifest_path)
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    images = []
    for img_info in manifest['images']:
        img_path = os.path.join(manifest_dir, img_info['path'])
        if os.path.exists(img_path):
            images.append({
                'path': img_path,
                'expected_faces': img_info['expected_faces']
            })
    
    if max_images and max_images < len(images):
        images = images[:max_images]
    
    if max_images and max_images > len(images):
        original = images.copy()
        while len(images) < max_images:
            for img in original:
                if len(images) >= max_images:
                    break
                images.append(img.copy())
    
    reference_path = os.path.join(manifest_dir, manifest['reference'])
    return images, reference_path


def run_benchmark(
    images: list,
    reference_path: str,
    output_dir: str,
    device: str = 'cpu',
    model_path: str = 'ckpts/sow_pyramid_a5_e3d2_remapped.pth',
    measure_memory: bool = False,
    use_cache: bool = False,
    optimize: bool = False
):
    os.makedirs(output_dir, exist_ok=True)
    
    if optimize:
        try:
            from training.optimization import setup_cpu_optimization
            setup_cpu_optimization()
        except ImportError:
            pass
    
    if measure_memory:
        tracemalloc.start()
    
    args, model_path = create_args(device, model_path)
    config = get_config()
    
    init_start = time.perf_counter()
    inference = Inference(config, args, model_path)
    init_time = time.perf_counter() - init_start
    
    reference = Image.open(reference_path).convert('RGB')
    
    cached_reference = None
    cache_time = 0
    if use_cache and hasattr(inference, 'cache_reference'):
        cache_start = time.perf_counter()
        cached_reference = inference.cache_reference(reference)
        cache_time = time.perf_counter() - cache_start
    
    results = []
    total_faces = 0
    total_processing_time = 0
    
    for i, img_info in enumerate(images):
        img_path = img_info['path']
        expected_faces = img_info['expected_faces']
        
        source = Image.open(img_path).convert('RGB')
        
        img_start = time.perf_counter()
        
        if cached_reference is not None and hasattr(inference, 'transfer_all_faces_cached'):
            result = inference.transfer_all_faces_cached(source, cached_reference, postprocess=True)
        else:
            result = inference.transfer_all_faces(source, reference, postprocess=True)
        
        img_time = time.perf_counter() - img_start
        total_processing_time += img_time
        
        faces_processed = expected_faces if result is not None else 0
        total_faces += faces_processed
        
        if result is not None:
            output_path = os.path.join(output_dir, f'result_{i}.png')
            result.save(output_path)
        
        results.append({
            'image': os.path.basename(img_path),
            'expected_faces': expected_faces,
            'faces_processed': faces_processed,
            'time_seconds': img_time,
            'success': result is not None
        })
    
    peak_memory_mb = 0
    if measure_memory:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = peak / 1024 / 1024
    
    return {
        'total_time_seconds': total_processing_time,
        'init_time_seconds': init_time,
        'cache_time_seconds': cache_time,
        'total_images': len(images),
        'total_faces': total_faces,
        'avg_time_per_image': total_processing_time / len(images) if images else 0,
        'avg_time_per_face': total_processing_time / total_faces if total_faces > 0 else 0,
        'peak_memory_mb': peak_memory_mb,
        'device': device,
        'use_cache': use_cache,
        'optimize': optimize,
        'per_image_results': results
    }


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark EleGANt makeup transfer performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/benchmark.py --images 2 --reference test_data/benchmark/reference.png
    python scripts/benchmark.py --images 8 --measure-memory --json results/metrics.json
        """
    )
    
    parser.add_argument('--images', type=int, default=2,
                        help='Number of images to process (default: 2)')
    parser.add_argument('--reference', type=str, 
                        default='test_data/benchmark/reference.png',
                        help='Path to reference image')
    parser.add_argument('--manifest', type=str,
                        default='test_data/benchmark/manifest.json',
                        help='Path to manifest.json with test images')
    parser.add_argument('--output', type=str, default='results/benchmark',
                        help='Directory to save output images')
    parser.add_argument('--json', type=str, default=None,
                        help='Path to save metrics as JSON')
    parser.add_argument('--device', type=str, default='cpu',
                        help='Device to use (cpu or cuda:N)')
    parser.add_argument('--model-path', type=str,
                        default='ckpts/sow_pyramid_a5_e3d2_remapped.pth',
                        help='Path to model weights')
    parser.add_argument('--cold-start', action='store_true',
                        help='Measure cold-start time (no warmup)')
    parser.add_argument('--measure-memory', action='store_true',
                        help='Track peak memory usage')
    parser.add_argument('--optimize', action='store_true',
                        help='Apply CPU optimizations')
    parser.add_argument('--use-cache', action='store_true',
                        help='Use reference caching if available')
    
    args = parser.parse_args()
    
    images, reference_path = load_images_from_manifest(args.manifest, args.images)
    
    if args.reference != 'test_data/benchmark/reference.png':
        reference_path = args.reference
    
    print(f"Benchmark Configuration:")
    print(f"  Images: {len(images)}")
    print(f"  Reference: {reference_path}")
    print(f"  Device: {args.device}")
    print(f"  Output: {args.output}")
    print(f"  Memory tracking: {args.measure_memory}")
    print(f"  Optimizations: {args.optimize}")
    print(f"  Use cache: {args.use_cache}")
    print()
    
    start_time = time.perf_counter()
    metrics = run_benchmark(
        images=images,
        reference_path=reference_path,
        output_dir=args.output,
        device=args.device,
        model_path=args.model_path,
        measure_memory=args.measure_memory,
        use_cache=args.use_cache,
        optimize=args.optimize
    )
    wall_time = time.perf_counter() - start_time
    metrics['wall_time_seconds'] = wall_time
    
    print("=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)
    print(f"Total processing time: {metrics['total_time_seconds']:.2f}s")
    print(f"Wall clock time: {metrics['wall_time_seconds']:.2f}s")
    print(f"Init time: {metrics['init_time_seconds']:.2f}s")
    if metrics['cache_time_seconds'] > 0:
        print(f"Cache time: {metrics['cache_time_seconds']:.2f}s")
    print(f"Images processed: {metrics['total_images']}")
    print(f"Total faces: {metrics['total_faces']}")
    print(f"Avg time per image: {metrics['avg_time_per_image']:.2f}s")
    print(f"Avg time per face: {metrics['avg_time_per_face']:.2f}s")
    if metrics['peak_memory_mb'] > 0:
        print(f"Peak memory: {metrics['peak_memory_mb']:.1f} MB")
    print()
    
    print("Per-image breakdown:")
    for r in metrics['per_image_results']:
        status = "OK" if r['success'] else "FAILED"
        print(f"  {r['image']}: {r['time_seconds']:.2f}s, {r['faces_processed']} faces [{status}]")
    
    if args.json:
        os.makedirs(os.path.dirname(args.json) or '.', exist_ok=True)
        with open(args.json, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\nMetrics saved to: {args.json}")


if __name__ == '__main__':
    main()
