# Decisions: Multi-Face Support

## Architectural Choices

### User Decisions (From Planning Phase)
1. **Partial Success Behavior**: Return None if any face fails (all-or-nothing)
2. **API Response Field**: Don't add `faces_processed` field (fully backward compatible)
3. **Multi-Face Behavior**: Apply same makeup to all detected faces
4. **Output Format**: Single image with all faces processed
5. **Test Strategy**: Manual verification only (no pytest setup)

_Agents append implementation decisions here._

---

## [2026-01-29 23:05] Task 2 Implementation Decisions

### Method Design
- **Backward Compatibility Strategy**: Delegate 1-face case to existing `preprocess()` rather than refactor
  - Rationale: Avoids any risk of behavioral changes for single-face scenarios
  - Tradeoff: Code duplication vs. safety

### Return Type Polymorphism
- Chose polymorphic return (None/tuple/list) over consistent list wrapping
  - Rationale: Makes 1-face case identical to existing `preprocess()` behavior
  - Benefit: Callers can upgrade incrementally without changing 1-face handling

### Comment Justification
- Kept one comment: "Backward compatible: single face uses existing path" (line 194)
  - Rationale: Explains non-obvious design decision (why delegate vs. process inline)
  - Removed unnecessary section marker comment per hook feedback

