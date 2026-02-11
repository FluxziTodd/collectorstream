import Foundation
import UIKit
import Vision
import CoreML

/// Service for identifying sports cards using multiple approaches:
/// 1. On-device Vision framework for edge detection and text recognition
/// 2. Ximilar API for card identification and pricing
/// 3. Local Core ML models for quick classification (future)
class CardIdentificationService {
    static let shared = CardIdentificationService()

    private let apiClient = APIClient.shared

    // MARK: - Ximilar API Configuration
    private let ximilarBaseURL = "https://api.ximilar.com/collectibles/v2"
    private var ximilarAPIKey: String? {
        // Store in keychain or environment
        ProcessInfo.processInfo.environment["XIMILAR_API_KEY"]
    }

    private init() {}

    // MARK: - Identify Card (Full Pipeline)
    func identifyCard(_ image: UIImage) async throws -> CardIdentification {
        // Step 1: Detect text using Vision for OCR
        let extractedText = try await extractText(from: image)

        // Step 2: Send to backend (which calls Ximilar or other services)
        guard let imageData = image.jpegData(compressionQuality: 0.95) else {
            throw IdentificationError.imageProcessingFailed
        }

        do {
            let response = try await apiClient.identifyCard(frontImageData: imageData, backImageData: nil)
            return CardIdentification(
                playerName: response.playerName,
                team: response.team,
                year: response.year,
                set: response.set,
                cardNumber: response.cardNumber,
                manufacturer: response.manufacturer,
                estimatedValue: response.estimatedValue,
                confidence: response.confidence,
                grading: response.grading.map { grading in
                    CardIdentification.Grading(
                        company: grading.company,
                        grade: grading.grade,
                        certNumber: grading.certNumber
                    )
                },
                extractedText: extractedText
            )
        } catch {
            // Fallback to OCR-only identification
            return CardIdentification(
                playerName: parsePlayerName(from: extractedText),
                team: parseTeam(from: extractedText),
                year: parseYear(from: extractedText),
                set: nil,
                cardNumber: parseCardNumber(from: extractedText),
                manufacturer: nil,
                estimatedValue: nil,
                confidence: 0.5,
                grading: nil,
                extractedText: extractedText
            )
        }
    }

    // MARK: - Extract Text using Vision OCR
    private func extractText(from image: UIImage) async throws -> [String] {
        guard let cgImage = image.cgImage else {
            throw IdentificationError.imageProcessingFailed
        }

        return try await withCheckedThrowingContinuation { continuation in
            let request = VNRecognizeTextRequest { request, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }

                guard let observations = request.results as? [VNRecognizedTextObservation] else {
                    continuation.resume(returning: [])
                    return
                }

                let texts = observations.compactMap { observation in
                    observation.topCandidates(1).first?.string
                }

                continuation.resume(returning: texts)
            }

            request.recognitionLevel = .accurate
            request.recognitionLanguages = ["en-US"]
            request.usesLanguageCorrection = true

            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

            DispatchQueue.global(qos: .userInitiated).async {
                do {
                    try handler.perform([request])
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }

    // MARK: - Detect Card Edges using Vision
    func detectCardBounds(in image: UIImage) async throws -> CGRect? {
        guard let cgImage = image.cgImage else {
            throw IdentificationError.imageProcessingFailed
        }

        return try await withCheckedThrowingContinuation { continuation in
            let request = VNDetectRectanglesRequest { request, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }

                guard let observations = request.results as? [VNRectangleObservation],
                      let bestMatch = observations.first else {
                    continuation.resume(returning: nil)
                    return
                }

                // Convert normalized coordinates to image coordinates
                let imageWidth = CGFloat(cgImage.width)
                let imageHeight = CGFloat(cgImage.height)

                let rect = CGRect(
                    x: bestMatch.boundingBox.origin.x * imageWidth,
                    y: (1 - bestMatch.boundingBox.origin.y - bestMatch.boundingBox.height) * imageHeight,
                    width: bestMatch.boundingBox.width * imageWidth,
                    height: bestMatch.boundingBox.height * imageHeight
                )

                continuation.resume(returning: rect)
            }

            // Configure for trading card dimensions
            request.minimumSize = 0.1
            request.maximumObservations = 1
            request.minimumAspectRatio = 0.6
            request.maximumAspectRatio = 0.8
            request.quadratureTolerance = 15

            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

            DispatchQueue.global(qos: .userInitiated).async {
                do {
                    try handler.perform([request])
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }

    // MARK: - Text Parsing Helpers
    private func parsePlayerName(from texts: [String]) -> String? {
        // Look for capitalized names (usually the largest/most prominent text)
        for text in texts {
            let words = text.components(separatedBy: " ")
            if words.count >= 2 {
                let allCapitalized = words.allSatisfy { word in
                    guard let first = word.first else { return false }
                    return first.isUppercase
                }
                if allCapitalized && !containsNumbers(text) {
                    return text
                }
            }
        }
        return texts.first
    }

    private func parseTeam(from texts: [String]) -> String? {
        let teamKeywords = [
            "Lakers", "Bulls", "Celtics", "Warriors", "Heat", "Nets",
            "Yankees", "Dodgers", "Red Sox", "Cubs", "Cardinals",
            "Chiefs", "Cowboys", "Patriots", "Packers", "49ers",
            "Bruins", "Rangers", "Maple Leafs", "Canadiens"
        ]

        for text in texts {
            for keyword in teamKeywords {
                if text.localizedCaseInsensitiveContains(keyword) {
                    return keyword
                }
            }
        }
        return nil
    }

    private func parseYear(from texts: [String]) -> String? {
        let yearPattern = #"\b(19[5-9]\d|20[0-2]\d)\b"#
        let regex = try? NSRegularExpression(pattern: yearPattern)

        for text in texts {
            let range = NSRange(text.startIndex..., in: text)
            if let match = regex?.firstMatch(in: text, range: range) {
                if let yearRange = Range(match.range, in: text) {
                    return String(text[yearRange])
                }
            }
        }
        return nil
    }

    private func parseCardNumber(from texts: [String]) -> String? {
        let numberPattern = #"#?\d+(/\d+)?"#
        let regex = try? NSRegularExpression(pattern: numberPattern)

        for text in texts {
            let range = NSRange(text.startIndex..., in: text)
            if let match = regex?.firstMatch(in: text, range: range) {
                if let numberRange = Range(match.range, in: text) {
                    return String(text[numberRange])
                }
            }
        }
        return nil
    }

    private func containsNumbers(_ text: String) -> Bool {
        text.rangeOfCharacter(from: .decimalDigits) != nil
    }
}

// MARK: - Card Identification Result
struct CardIdentification {
    var playerName: String?
    var team: String?
    var year: String?
    var set: String?
    var cardNumber: String?
    var manufacturer: String?
    var estimatedValue: Double?
    var confidence: Double
    var grading: Grading?
    var extractedText: [String]

    struct Grading {
        var company: String?
        var grade: String?
        var certNumber: String?
    }
}

// MARK: - Identification Error
enum IdentificationError: Error {
    case imageProcessingFailed
    case networkError
    case noCardDetected
    case apiError(String)

    var localizedDescription: String {
        switch self {
        case .imageProcessingFailed:
            return "Failed to process the image"
        case .networkError:
            return "Network connection error"
        case .noCardDetected:
            return "No card detected in image"
        case .apiError(let message):
            return message
        }
    }
}
