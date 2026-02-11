import UIKit
import CoreImage
import Accelerate

/// Utility for detecting blurry images using Laplacian variance
class BlurDetector {

    /// Blur detection thresholds
    /// Lower values = blurrier image
    /// Higher values = sharper image
    static let sharpThreshold: Double = 100.0  // Minimum acceptable sharpness
    static let idealThreshold: Double = 200.0  // Good quality threshold

    /// Detects if an image is blurry using Laplacian variance
    /// - Parameter image: The UIImage to analyze
    /// - Returns: Tuple of (isBlurry: Bool, sharpness: Double)
    static func detectBlur(in image: UIImage) -> (isBlurry: Bool, sharpness: Double) {
        let sharpness = calculateLaplacianVariance(image)
        let isBlurry = sharpness < sharpThreshold

        print("📊 Blur Detection - Sharpness: \(String(format: "%.1f", sharpness)) (threshold: \(String(format: "%.1f", sharpThreshold)))")

        if isBlurry {
            print("⚠️ Image is BLURRY")
        } else if sharpness >= idealThreshold {
            print("✅ Image is SHARP")
        } else {
            print("✓ Image is ACCEPTABLE")
        }

        return (isBlurry, sharpness)
    }

    /// Calculates Laplacian variance (edge detection metric for blur)
    /// High variance = sharp edges = not blurry
    /// Low variance = soft edges = blurry
    private static func calculateLaplacianVariance(_ image: UIImage) -> Double {
        // Convert to grayscale CIImage
        guard let ciImage = CIImage(image: image) else {
            print("❌ Failed to create CIImage")
            return 0
        }

        // Create grayscale filter
        let context = CIContext(options: nil)
        let grayscaleFilter = CIFilter(name: "CIPhotoEffectMono")
        grayscaleFilter?.setValue(ciImage, forKey: kCIInputImageKey)

        guard let grayscaleOutput = grayscaleFilter?.outputImage,
              let cgImage = context.createCGImage(grayscaleOutput, from: grayscaleOutput.extent) else {
            print("❌ Failed to convert to grayscale")
            return 0
        }

        // Convert to raw pixel data
        guard let pixelData = extractPixelData(from: cgImage) else {
            print("❌ Failed to extract pixel data")
            return 0
        }

        let width = cgImage.width
        let height = cgImage.height

        // Apply Laplacian kernel (edge detection)
        // Kernel:
        // [ 0  1  0]
        // [ 1 -4  1]
        // [ 0  1  0]
        var laplacian = [Double](repeating: 0, count: width * height)

        for y in 1..<(height - 1) {
            for x in 1..<(width - 1) {
                let idx = y * width + x

                let center = Double(pixelData[idx])
                let top = Double(pixelData[(y - 1) * width + x])
                let bottom = Double(pixelData[(y + 1) * width + x])
                let left = Double(pixelData[y * width + (x - 1)])
                let right = Double(pixelData[y * width + (x + 1)])

                laplacian[idx] = abs(-4 * center + top + bottom + left + right)
            }
        }

        // Calculate variance of Laplacian
        let mean = laplacian.reduce(0, +) / Double(laplacian.count)
        let variance = laplacian.map { pow($0 - mean, 2) }.reduce(0, +) / Double(laplacian.count)

        return variance
    }

    /// Extracts grayscale pixel data from CGImage
    private static func extractPixelData(from cgImage: CGImage) -> [UInt8]? {
        let width = cgImage.width
        let height = cgImage.height
        let bytesPerPixel = 1
        let bytesPerRow = bytesPerPixel * width
        let bitsPerComponent = 8

        var pixelData = [UInt8](repeating: 0, count: width * height)

        let colorSpace = CGColorSpaceCreateDeviceGray()
        guard let context = CGContext(
            data: &pixelData,
            width: width,
            height: height,
            bitsPerComponent: bitsPerComponent,
            bytesPerRow: bytesPerRow,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.none.rawValue
        ) else {
            return nil
        }

        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))

        return pixelData
    }

    /// Gets a quality rating for the sharpness score
    static func getQualityRating(sharpness: Double) -> String {
        if sharpness >= idealThreshold {
            return "Excellent"
        } else if sharpness >= sharpThreshold * 1.5 {
            return "Good"
        } else if sharpness >= sharpThreshold {
            return "Acceptable"
        } else if sharpness >= sharpThreshold * 0.5 {
            return "Poor"
        } else {
            return "Very Blurry"
        }
    }
}
