# Learnings: Multi-Face Support

## Conventions & Patterns

_Agents append findings here after each task completion._

---

## Task 1: Test Fixtures & Baseline (2025-01-29)

### Key Findings

1. **Face Detection Reliability**
   - dlib.detect() requires realistic face images (synthetic faces don't work)
   - Downloaded real portrait images from Unsplash work reliably
   - Two-face image created by combining two single-face images side-by-side
   - All 4 fixtures validated: single_face (1), two_faces (2), no_face (0), makeup_reference (1)

2. **PyTorch Compatibility Issue**
   - PyTorch 2.x requires `weights_only=False` parameter in torch.load()
   - Fixed in training/solver.py line 22
   - System has no CUDA - must run with `--gpu cpu` flag

3. **Baseline Generation**
   - demo.py successfully generates baseline with single_face.jpg
   - Output: result/demo/result_single_face_full.png (177.3 KB)
   - Copied to baseline/expected_single_face_result.png for regression testing
   - Image dimensions: 400x500 pixels (matches input)

4. **Directory Structure Created**
   - tests/fixtures/ - contains 4 test images (total ~112 KB)
   - baseline/ - contains expected_single_face_result.png (177.3 KB)
   - .sisyphus/evidence/ - ready for verification screenshots

### Acceptance Criteria Status
- ✓ Directory structure created
- ✓ All 4 test images present and valid
- ✓ Face detection validation passed (4/4 tests)
- ✓ Baseline generated from current code
- ✓ Baseline file > 100KB (177.3 KB)

### Next Steps
- Task 2: Modify PreProcess to support all faces
- Task 3: Add multi-face transfer logic to Inference
- Tasks 4-6: Update entry points (demo.py, api.py, app.py)


## [2026-01-29 23:05] Task 2: Multi-Face Preprocessing Implementation

### Pattern Applied
- Duplicated core preprocessing logic from `preprocess()` for each face in multi-face scenario
- Maintained backward compatibility by delegating 1-face case to existing `preprocess()`
- Return type polymorphism: None (0 faces) / tuple (1 face) / list (≥2 faces)

### Key Implementation Details
- Used `futils.dlib.detect(image)` to get all faces (returns dlib.rectangles)
- For each face rectangle, applied same pipeline: crop → face parse → landmarks → resize
- Critical: Used `cropped_image.width` (not original `image.width`) for landmarks scaling in multi-face loop
- Preserved all landmark adjustments from original (distinguish upper/lower lips, lines 221-227)

### Testing Approach
- All 5 acceptance criteria tests passed:
  1. Method signature verification ✓
  2. 0 faces → None ✓
  3. 1 face → tuple ✓
  4. 2 faces → list of 2 tuples ✓
  5. No regression on existing `preprocess()` ✓
- Used test fixtures from Task 1 (no_face.jpg, single_face.jpg, two_faces.jpg)

### Tradeoffs Made
- Chose code duplication over refactoring `preprocess()` to avoid signature change
- Accepted ~50 lines of duplicated logic to maintain strict backward compatibility
- Alternative (rejected): Add optional `face_rect` parameter to `preprocess()` would be cleaner but risks breaking callers

