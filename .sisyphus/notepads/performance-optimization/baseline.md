# Performance Optimization Baseline Measurements

**Date**: 2026-01-30
**Session**: ses_3f59462c7ffewGW26qPjqDkZwL

## Test Configuration

- **Platform**: macOS (darwin)
- **Device**: CPU
- **Model**: ckpts/sow_pyramid_a5_e3d2_remapped.pth
- **Test Images**: 2 unique images (single_face.jpg, two_faces.jpg), repeated for 8-image test

## Baseline Results (2 Images, 3 Faces)

| Metric | Value |
|--------|-------|
| Total processing time | 3.10s |
| Wall clock time | 3.43s |
| Init time | 0.28s |
| Images processed | 2 |
| Total faces | 3 |
| Avg time per image | 1.55s |
| Avg time per face | 1.03s |
| Peak memory | 137.1 MB |

### Per-Image Breakdown
- single_face.jpg: 1.40s, 1 face
- two_faces.jpg: 1.70s, 2 faces

## Baseline Results (8 Images, 12 Faces)

| Metric | Value |
|--------|-------|
| Total processing time | 10.81s |
| Wall clock time | 11.19s |
| Init time | 0.26s |
| Images processed | 8 |
| Total faces | 12 |
| Avg time per image | 1.35s |
| Avg time per face | 0.90s |
| Peak memory | 137.1 MB |

## Extrapolation to Target Workload

**Target**: 8 images × 4-5 faces = 36 faces in < 60 seconds

Based on baseline (0.90s/face):
- 36 faces × 0.90s = **32.4 seconds** (estimated)

**Note**: This baseline was measured on macOS. User's target hardware is Intel i5-12400 which may have different performance characteristics.

## Observations

1. **Memory usage is stable**: 137.1 MB peak regardless of image count - model memory dominates
2. **Per-face time decreases with more faces**: 1.03s (3 faces) → 0.90s (12 faces) - likely due to warmup
3. **Initialization is fast**: ~0.27s average
4. **Current performance may already meet target**: Extrapolated 32.4s < 60s target

## Optimization Opportunities Still Worth Pursuing

Even if baseline meets target on this hardware:
1. **Reference caching**: Currently preprocessing reference for each image (redundant)
2. **PyTorch threading**: May not be optimally configured
3. **Intel-specific optimizations**: MKL, oneDNN settings for user's i5-12400

## Files Generated

- `results/baseline/metrics.json` - 2-image baseline metrics
- `results/baseline/*.png` - 2-image baseline output images
- `results/baseline_8/metrics.json` - 8-image baseline metrics
- `results/baseline_8/*.png` - 8-image baseline output images
