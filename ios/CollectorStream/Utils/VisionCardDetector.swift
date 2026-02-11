import Foundation
import Vision
import UIKit
import CoreGraphics

/// Result of Vision-based card detection
struct VisionCardResult {
    let normalizedRect: CGRect
    let confidence: Float
    let isLandscape: Bool
}

/// Detects trading card rectangles using Vision framework
final class VisionCardDetector {

    /// Detect a trading card in the captured image
    /// - Parameters:
    ///   - image: The captured photo
    ///   - completion: Called with result (or nil if detection failed)
    static func detectCard(
        in image: UIImage,
        completion: @escaping (VisionCardResult?) -> Void
    ) {
        guard let cgImage = image.cgImage else {
            completion(nil)
            return
        }

        let request = VNDetectRectanglesRequest { request, error in
            if let error = error {
                print("🔍 Vision error: \(error.localizedDescription)")
                completion(nil)
                return
            }

            guard let observations = request.results as? [VNRectangleObservation],
                  let bestObservation = observations.first else {
                print("🔍 No card detected")
                completion(nil)
                return
            }

            let rect = bestObservation.boundingBox
            let isLandscape = rect.width > rect.height

            print("🔍 Card detected!")
            print("   Position: (\(String(format: "%.3f", rect.origin.x)), \(String(format: "%.3f", rect.origin.y)))")
            print("   Size: \(String(format: "%.3f", rect.width))x\(String(format: "%.3f", rect.height))")
            print("   Confidence: \(String(format: "%.2f", bestObservation.confidence))")
            print("   Orientation: \(isLandscape ? "Landscape" : "Portrait")")

            completion(VisionCardResult(
                normalizedRect: rect,
                confidence: bestObservation.confidence,
                isLandscape: isLandscape
            ))
        }

        // Tuned specifically for trading cards (2.5" x 3.5" aspect ≈ 0.714)
        request.maximumObservations = 1
        request.minimumConfidence = 0.6
        request.minimumAspectRatio = 0.65  // Allow slight variation
        request.maximumAspectRatio = 0.80  // Allow slight variation
        request.quadratureTolerance = 20   // Allow slight skew

        let handler = VNImageRequestHandler(
            cgImage: cgImage,
            orientation: .up,
            options: [:]
        )

        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try handler.perform([request])
            } catch {
                print("🔍 Vision request failed: \(error.localizedDescription)")
                completion(nil)
            }
        }
    }

    /// Crop image to detected card rectangle
    /// - Parameters:
    ///   - image: The captured photo
    ///   - result: Vision detection result
    /// - Returns: Cropped image of just the card
    static func cropToCard(
        image: UIImage,
        result: VisionCardResult
    ) -> UIImage {
        guard let cgImage = image.cgImage else { return image }

        let width = CGFloat(cgImage.width)
        let height = CGFloat(cgImage.height)
        let rect = result.normalizedRect

        // Convert normalized rect to pixel coordinates with Y-inversion
        let cropRect = CGRect(
            x: rect.origin.x * width,
            y: (1 - rect.origin.y - rect.height) * height,
            width: rect.width * width,
            height: rect.height * height
        )

        print("🔍 Cropping to detected card:")
        print("   Crop pixels: (\(Int(cropRect.origin.x)), \(Int(cropRect.origin.y))) \(Int(cropRect.width))x\(Int(cropRect.height))")

        guard let croppedCG = cgImage.cropping(to: cropRect) else {
            return image
        }

        let croppedImage = UIImage(
            cgImage: croppedCG,
            scale: image.scale,
            orientation: image.imageOrientation
        )

        // Rotate landscape cards to portrait for consistency
        return result.isLandscape ? rotateToPortrait(croppedImage) : croppedImage
    }

    /// Rotate landscape card to portrait orientation
    private static func rotateToPortrait(_ image: UIImage) -> UIImage {
        guard let cgImage = image.cgImage else { return image }
        return UIImage(
            cgImage: cgImage,
            scale: image.scale,
            orientation: .right
        )
    }
}
