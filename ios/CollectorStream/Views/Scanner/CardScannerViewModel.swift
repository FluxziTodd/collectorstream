import SwiftUI
import AVFoundation
import Vision

/// View model for card scanning functionality
@MainActor
class CardScannerViewModel: ObservableObject {
    // MARK: - Scan State
    enum ScanState: Equatable {
        case ready
        case scanning
        case reviewFront
        case scanningBack
        case reviewBack
        case processing
        case identified
        case error(String)
    }

    // MARK: - Published Properties
    @Published var scanState: ScanState = .ready
    @Published var frontImage: UIImage?
    @Published var backImage: UIImage?
    @Published var identification: APIClient.CardIdentificationResponse?

    // Editable fields (pre-populated from identification)
    @Published var editablePlayerName = ""
    @Published var editableTeam = ""
    @Published var editableYear = ""
    @Published var editableSet = ""
    @Published var editableCardNumber = ""
    @Published var editableSport: Card.Sport = .baseball
    @Published var editableCondition: Card.Condition?
    @Published var editablePurchasePrice: Double?

    // Camera
    @Published var isCameraAuthorized = false

    // Blur detection
    @Published var blurWarningMessage: String?
    @Published var showBlurWarning = false

    private let apiClient = APIClient.shared

    // MARK: - Camera Authorization
    func checkCameraAuthorization() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            isCameraAuthorized = true
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    self?.isCameraAuthorized = granted
                }
            }
        default:
            isCameraAuthorized = false
        }
    }

    // MARK: - Start Scanning
    func startScanning() {
        checkCameraAuthorization()
        scanState = .scanning
    }

    // MARK: - Capture Front
    func captureFront(_ image: UIImage) {
        frontImage = image
        scanState = .reviewFront
    }

    // MARK: - Proceed to Back
    func proceedToBack() {
        scanState = .scanningBack
    }

    // MARK: - Capture Back
    func captureBack(_ image: UIImage) {
        backImage = image
        scanState = .reviewBack
    }

    // MARK: - Retake
    func retakeFront() {
        frontImage = nil
        scanState = .scanning
    }

    func retakeBack() {
        backImage = nil
        scanState = .scanningBack
    }

    // MARK: - Process Card
    func processCard() async {
        guard let frontImage = frontImage else {
            scanState = .error("No front image captured")
            return
        }

        scanState = .processing

        // Convert images to JPEG data
        guard let frontImageData = frontImage.jpegData(compressionQuality: 0.95) else {
            scanState = .error("Failed to process front image")
            return
        }

        let backImageData = backImage?.jpegData(compressionQuality: 0.95)

        do {
            // Call identification API with BOTH images
            let response = try await apiClient.identifyCard(frontImageData: frontImageData, backImageData: backImageData)
            identification = response

            // Pre-populate editable fields
            editablePlayerName = response.playerName ?? ""
            editableTeam = response.team ?? ""
            editableYear = response.year ?? ""
            editableSet = response.set ?? ""
            editableCardNumber = response.cardNumber ?? ""

            // Map sport from API response
            if let sportString = response.sport?.lowercased() {
                print("🏀 Detected sport: \(sportString)")
                switch sportString {
                case "baseball", "mlb":
                    editableSport = .baseball
                case "basketball", "nba":
                    editableSport = .basketball
                case "football", "nfl":
                    editableSport = .football
                case "hockey", "nhl":
                    editableSport = .hockey
                case "soccer":
                    editableSport = .soccer
                case "wnba":
                    editableSport = .basketball  // WNBA cards use basketball type
                    print("ℹ️ WNBA card detected - using basketball sport type")
                default:
                    print("⚠️ Unknown sport '\(sportString)' - defaulting to baseball")
                    editableSport = .baseball
                }
            }

            scanState = .identified
        } catch let error as APIError {
            scanState = .error(error.userMessage)
        } catch {
            scanState = .error("Failed to identify card. Please try again.")
        }
    }

    // MARK: - Blur Warning
    func showBlurWarning(sharpness: Double) {
        let quality = BlurDetector.getQualityRating(sharpness: sharpness)
        blurWarningMessage = "Image too blurry (\(quality)). Hold steady and try again."
        showBlurWarning = true

        // Auto-dismiss after 3 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
            self?.showBlurWarning = false
        }
    }

    // MARK: - Reset
    func reset() {
        scanState = .ready
        frontImage = nil
        backImage = nil
        identification = nil
        editablePlayerName = ""
        editableTeam = ""
        editableYear = ""
        editableSet = ""
        editableCardNumber = ""
        editableSport = .baseball
        editableCondition = nil
        editablePurchasePrice = nil
        showBlurWarning = false
        blurWarningMessage = nil
    }
}
