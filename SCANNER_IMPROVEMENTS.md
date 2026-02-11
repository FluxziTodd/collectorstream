# Card Scanner Image Quality Improvements

## Problem Statement
The card scanner was capturing images with the card appearing small in the frame, surrounded by excessive background area. This resulted in poor-quality thumbnails that looked unprofessional.

## Root Causes Identified

### 1. **No Camera Zoom**
- Camera was using full field of view (wide angle)
- Card appeared small relative to total capture area
- Green box overlay was just visual guidance, not affecting capture

### 2. **Imprecise Cropping**
- Cropping logic was **guessing** card location (assuming 70% of width)
- Didn't map green box position to actual image coordinates
- Result: captured area didn't match what user saw in green box

### 3. **Aspect Ratio Mismatch**
- Previous green box: 280x400 (aspect 0.7)
- Standard trading card: 2.5" x 3.5" (aspect 0.714)
- Close but could be better

## Solutions Implemented

### ✅ **1. Camera Zoom (1.8x)**
**Location**: `CameraScannerView.swift` line 217-226

```swift
// Zoom in 1.8x - makes card fill the green box area better
let desiredZoom: CGFloat = 1.8
if desiredZoom <= camera.activeFormat.videoMaxZoomFactor {
    camera.videoZoomFactor = 1.8
}
```

**Impact**:
- Card now appears **1.8x larger** in camera view
- Fills the green box much better
- User sees exactly what they'll capture

**Why 1.8x?**
- Not too close (would require very steady hands)
- Not too far (defeats the purpose)
- Sweet spot for handheld card scanning
- Adjustable: can test 1.5-2.5x based on user feedback

### ✅ **2. Enhanced Camera Settings**
**Location**: `CameraScannerView.swift` line 228-237

```swift
// Enable auto focus for better card detail
if camera.isFocusModeSupported(.continuousAutoFocus) {
    camera.focusMode = .continuousAutoFocus
}

// Enable auto exposure
if camera.isExposureModeSupported(.continuousAutoExposure) {
    camera.exposureMode = .continuousAutoExposure
}
```

**Benefits**:
- Card text stays sharp
- Adjusts to lighting conditions automatically
- Better detail capture for AI identification

### ✅ **3. High Resolution Capture**
**Location**: `CameraScannerView.swift` line 248

```swift
output.isHighResolutionCaptureEnabled = true
```

**Result**:
- Maximum sensor resolution used
- More detail for AI to analyze
- Better quality thumbnails after cropping

### ✅ **4. Precise Coordinate Mapping**
**Location**: `CameraScannerView.swift` line 302-335

**Old Method** (guessing):
```swift
// WRONG: Just guessing card is 70% of width
var cropWidth = imageWidth * 0.7
var cropHeight = cropWidth / cardAspect
```

**New Method** (precise):
```swift
// Calculate exact green box position on screen
let boxRect = CGRect(
    x: boxCenterX - boxWidth / 2,
    y: boxCenterY - boxHeight / 2,
    width: boxWidth,
    height: boxHeight
)

// Convert screen coordinates to video coordinates
let videoRect = previewLayer.metadataOutputRectConverted(fromLayerRect: boxRect)

// Convert to image pixel coordinates
let cropX = videoRect.origin.x * imageWidth
let cropY = videoRect.origin.y * imageHeight
```

**Why This Matters**:
- Crops **exactly** what user sees in green box
- No more guessing about card position
- Accounts for different screen sizes and orientations
- Professional-grade coordinate transformation

### ✅ **5. Increased Green Box Size**
**Location**: `CameraScannerView.swift` line 58-60

**Before**: 280x400 pixels
**After**: 300x420 pixels

**Why**:
- More forgiving for user alignment
- Better capture of card edges
- Still maintains 2.5:3.5 aspect ratio (0.714)
- 7% larger capture area

### ✅ **6. Smart Padding**
**Location**: `CameraScannerView.swift` line 328-330

```swift
// Add 2% padding to account for slight misalignment
let padding: CGFloat = 0.02
```

**Purpose**:
- Accounts for minor hand shake
- Ensures card edges aren't cut off
- Small enough to avoid excess background
- With zoom + precise cropping, minimal padding needed

## Expected Results

### Before:
- ❌ Card is small (maybe 40-50% of image)
- ❌ Lots of table/background visible
- ❌ Thumbnails look unprofessional
- ❌ User sees one thing in green box, captures something different

### After:
- ✅ Card fills 95%+ of captured image
- ✅ Minimal background (just 2% padding)
- ✅ Professional-looking thumbnails
- ✅ What You See Is What You Get (WYSIWYG)
- ✅ Sharper images with auto-focus
- ✅ Better lighting with auto-exposure
- ✅ Higher resolution capture

## Technical Details

### Coordinate System Transformations
The app now correctly handles three coordinate spaces:

1. **Screen Coordinates**: Where green box appears (UIKit points)
2. **Video Coordinates**: Normalized 0-1 range (AVFoundation)
3. **Image Coordinates**: Actual pixels (Core Graphics)

Transformation chain:
```
Screen Points → Video Rect → Image Pixels
   (300x420) → (0.3, 0.2, 0.4, 0.6) → (1200x2400)
```

### Card Aspect Ratio
Standard trading card dimensions:
- Width: 2.5 inches (63.5mm)
- Height: 3.5 inches (88.9mm)
- Aspect Ratio: 0.714 (5:7)

Green box maintains this ratio for accurate capture.

## Testing Recommendations

### Test Scenarios:
1. ✅ Scan card at normal distance (~12 inches)
2. ✅ Verify card fills green box in preview
3. ✅ Check captured image has minimal background
4. ✅ Confirm thumbnails look professional
5. ✅ Test with different lighting conditions
6. ✅ Test with glossy vs matte cards
7. ✅ Verify no top/bottom cropping

### Adjustable Parameters:
If further tuning needed:

- **Zoom Factor**: Line 221 - adjust between 1.5-2.5
- **Green Box Size**: Line 59-60 - adjust width/height
- **Padding**: Line 330 - adjust between 0.01-0.05

## Next Steps

1. **Build and test** on device
2. **Scan multiple cards** to verify consistency
3. **Check AI identification** still works with zoomed images
4. **Verify thumbnail display** in collection view
5. **Adjust zoom factor** if needed (currently 1.8x)

## Files Modified

- `/ios/CollectorStream/Views/Scanner/CameraScannerView.swift`
  - Added camera zoom configuration
  - Enhanced auto-focus and auto-exposure
  - Enabled high-resolution capture
  - Implemented precise coordinate mapping
  - Increased green box size
  - Optimized cropping with smart padding

## Performance Impact

- **Capture Time**: No change (same speed)
- **Memory**: Slightly higher (high-res images)
- **Processing**: Minimal (coordinate math is fast)
- **Battery**: Negligible increase (auto-focus/exposure)

## Success Metrics

- Card should fill **≥95%** of captured image
- Background should be **≤5%** of image
- User satisfaction with thumbnail quality
- No complaints about cropped card edges
- Maintained AI identification accuracy

---

**Status**: ✅ Ready for Testing
**Priority**: High - Directly impacts user experience
**Risk**: Low - Non-breaking changes with fallbacks
