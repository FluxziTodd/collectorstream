import SwiftUI
import AVFoundation
import Vision

/// Camera view for scanning cards with edge detection
struct CameraScannerView: View {
    @ObservedObject var viewModel: CardScannerViewModel
    @State private var captureTriggered = false
    @State private var greenBoxFrame: CGRect = .zero

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Camera Preview
                CameraPreview(
                    viewModel: viewModel,
                    captureTriggered: captureTriggered,
                    targetBoxFrame: greenBoxFrame
                )
                .ignoresSafeArea()

                // Overlay
                VStack {
                    // Instructions
                    Text(viewModel.scanState == .scanning ? "Scan Front of Card" : "Scan Back of Card")
                        .font(Theme.Typography.headline)
                        .foregroundColor(.white)
                        .padding(.vertical, Theme.Spacing.sm)
                        .padding(.horizontal, Theme.Spacing.md)
                        .background(Color.black.opacity(0.6))
                        .cornerRadius(Theme.CornerRadius.small)
                        .padding(.top, Theme.Spacing.lg)

                    Spacer()

                    // Card Frame Guide with position tracking
                    CardFrameGuide()
                        .background(
                            GeometryReader { frameGeometry in
                                Color.clear.preference(
                                    key: FramePreferenceKey.self,
                                    value: frameGeometry.frame(in: .global)
                                )
                            }
                        )

                    Spacer()

                    // Capture Button
                    Button(action: {
                        captureTriggered.toggle()
                    }) {
                        ZStack {
                            Circle()
                                .fill(Color.white)
                                .frame(width: 70, height: 70)

                            Circle()
                                .stroke(Theme.Colors.accent, lineWidth: 4)
                                .frame(width: 80, height: 80)
                        }
                    }
                    .padding(.bottom, Theme.Spacing.xl)

                    // Blur Warning
                    if viewModel.showBlurWarning {
                        VStack {
                            HStack(spacing: 12) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.system(size: 20))
                                    .foregroundColor(.yellow)

                                Text(viewModel.blurWarningMessage ?? "Image too blurry")
                                    .font(Theme.Typography.subheadline)
                                    .foregroundColor(.white)
                            }
                            .padding()
                            .background(Color.black.opacity(0.85))
                            .cornerRadius(12)
                            .shadow(radius: 8)
                        }
                        .padding(.bottom, Theme.Spacing.lg)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                        .animation(.spring(), value: viewModel.showBlurWarning)
                    }
                }
            }
            .onPreferenceChange(FramePreferenceKey.self) { frame in
                greenBoxFrame = frame
            }
        }
    }
}

// MARK: - Frame Preference Key
struct FramePreferenceKey: PreferenceKey {
    static var defaultValue: CGRect = .zero
    static func reduce(value: inout CGRect, nextValue: () -> CGRect) {
        value = nextValue()
    }
}

// MARK: - Card Frame Guide
struct CardFrameGuide: View {
    static let frameWidth: CGFloat = 300
    static let frameHeight: CGFloat = 420

    var body: some View {
        ZStack {
            Rectangle()
                .fill(Color.black.opacity(0.5))
                .mask(
                    ZStack {
                        Rectangle()
                        RoundedRectangle(cornerRadius: 12)
                            .frame(width: CardFrameGuide.frameWidth, height: CardFrameGuide.frameHeight)
                            .blendMode(.destinationOut)
                    }
                    .compositingGroup()
                )

            RoundedRectangle(cornerRadius: 12)
                .stroke(Theme.Colors.accent, lineWidth: 3)
                .frame(width: CardFrameGuide.frameWidth, height: CardFrameGuide.frameHeight)

            CardFrameCorners()
        }
    }
}

struct CardFrameCorners: View {
    var body: some View {
        ZStack {
            VStack {
                HStack {
                    CornerShape(rotation: 0)
                    Spacer()
                }
                Spacer()
            }
            VStack {
                HStack {
                    Spacer()
                    CornerShape(rotation: 90)
                }
                Spacer()
            }
            VStack {
                Spacer()
                HStack {
                    CornerShape(rotation: 270)
                    Spacer()
                }
            }
            VStack {
                Spacer()
                HStack {
                    Spacer()
                    CornerShape(rotation: 180)
                }
            }
        }
        .frame(width: CardFrameGuide.frameWidth, height: CardFrameGuide.frameHeight)
    }
}

struct CornerShape: View {
    let rotation: Double

    var body: some View {
        Path { path in
            path.move(to: CGPoint(x: 0, y: 25))
            path.addLine(to: CGPoint(x: 0, y: 0))
            path.addLine(to: CGPoint(x: 25, y: 0))
        }
        .stroke(Theme.Colors.accent, style: StrokeStyle(lineWidth: 4, lineCap: .round))
        .rotationEffect(.degrees(rotation))
        .frame(width: 25, height: 25)
    }
}

// MARK: - Camera Preview
struct CameraPreview: UIViewRepresentable {
    @ObservedObject var viewModel: CardScannerViewModel
    var captureTriggered: Bool
    var targetBoxFrame: CGRect

    func makeUIView(context: Context) -> CameraPreviewView {
        let view = CameraPreviewView()
        view.delegate = context.coordinator
        return view
    }

    func updateUIView(_ uiView: CameraPreviewView, context: Context) {
        // Update target box frame
        uiView.targetBoxFrame = targetBoxFrame

        // Handle capture trigger
        if captureTriggered != context.coordinator.lastCaptureState {
            context.coordinator.lastCaptureState = captureTriggered
            if captureTriggered {
                uiView.capturePhoto()
            }
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(viewModel: viewModel)
    }

    class Coordinator: NSObject, CameraPreviewViewDelegate {
        let viewModel: CardScannerViewModel
        var lastCaptureState: Bool = false

        init(viewModel: CardScannerViewModel) {
            self.viewModel = viewModel
        }

        func didCaptureImage(_ image: UIImage) {
            Task { @MainActor in
                if viewModel.scanState == .scanning {
                    viewModel.captureFront(image)
                } else if viewModel.scanState == .scanningBack {
                    viewModel.captureBack(image)
                }
            }
        }

        func didRejectBlurryImage(sharpness: Double) {
            Task { @MainActor in
                viewModel.showBlurWarning(sharpness: sharpness)
            }
        }
    }
}

// MARK: - Camera Preview UIView
protocol CameraPreviewViewDelegate: AnyObject {
    func didCaptureImage(_ image: UIImage)
    func didRejectBlurryImage(sharpness: Double)
}

class CameraPreviewView: UIView {
    weak var delegate: CameraPreviewViewDelegate?
    var targetBoxFrame: CGRect = .zero

    private var captureSession: AVCaptureSession?
    private var videoPreviewLayer: AVCaptureVideoPreviewLayer?
    private var photoOutput: AVCapturePhotoOutput?

    override init(frame: CGRect) {
        super.init(frame: frame)
        setupCamera()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupCamera()
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        videoPreviewLayer?.frame = bounds
    }

    private func setupCamera() {
        let session = AVCaptureSession()
        session.sessionPreset = .photo

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: camera) else {
            return
        }

        // Lock camera config
        do {
            try camera.lockForConfiguration()

            // Stable frame rate
            camera.activeVideoMinFrameDuration = CMTime(value: 1, timescale: 30)
            camera.activeVideoMaxFrameDuration = CMTime(value: 1, timescale: 30)

            // Auto focus
            if camera.isFocusModeSupported(.continuousAutoFocus) {
                camera.focusMode = .continuousAutoFocus
            }

            // Auto exposure
            if camera.isExposureModeSupported(.continuousAutoExposure) {
                camera.exposureMode = .continuousAutoExposure
            }

            camera.unlockForConfiguration()
        } catch {
            print("📸 Camera config failed: \(error)")
        }

        if session.canAddInput(input) {
            session.addInput(input)
        }

        let output = AVCapturePhotoOutput()
        output.isHighResolutionCaptureEnabled = true

        if session.canAddOutput(output) {
            session.addOutput(output)
            photoOutput = output
        }

        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill  // CRITICAL
        previewLayer.connection?.videoOrientation = .portrait
        layer.addSublayer(previewLayer)
        videoPreviewLayer = previewLayer

        captureSession = session

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.captureSession?.startRunning()
        }

        let tapGesture = UITapGestureRecognizer(target: self, action: #selector(handleTap))
        addGestureRecognizer(tapGesture)
    }

    @objc private func handleTap() {
        capturePhoto()
    }

    func capturePhoto() {
        guard let photoOutput = photoOutput else { return }

        // Add stabilization delay to reduce motion blur
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
            guard let self = self else { return }

            let settings = AVCapturePhotoSettings()
            settings.flashMode = .off

            // Enable high quality capture (only if supported by device)
            if #available(iOS 13.0, *) {
                // Use the highest quality supported by this device
                settings.photoQualityPrioritization = photoOutput.maxPhotoQualityPrioritization
            }

            photoOutput.capturePhoto(with: settings, delegate: self)
        }
    }

    deinit {
        captureSession?.stopRunning()
    }

    // MARK: - Metadata rect conversion (Apple's way - already aspect-fill safe)
    private func metadataRect(for cropBoxFrame: CGRect) -> CGRect {
        guard let previewLayer = videoPreviewLayer, !cropBoxFrame.isEmpty else {
            return CGRect(x: 0.25, y: 0.25, width: 0.5, height: 0.5)
        }

        // Convert crop box to normalized metadata rect
        // metadataOutputRectConverted already accounts for .resizeAspectFill
        let normalizedRect = previewLayer.metadataOutputRectConverted(fromLayerRect: cropBoxFrame)

        print("📸 Crop box: \(Int(cropBoxFrame.width))x\(Int(cropBoxFrame.height))")
        print("📸 Screen rect: (\(Int(cropBoxFrame.origin.x)), \(Int(cropBoxFrame.origin.y))) \(Int(cropBoxFrame.width))x\(Int(cropBoxFrame.height))")
        print("📸 Normalized rect: (\(String(format: "%.3f", normalizedRect.origin.x)), \(String(format: "%.3f", normalizedRect.origin.y))) \(String(format: "%.3f", normalizedRect.width))x\(String(format: "%.3f", normalizedRect.height))")

        return normalizedRect
    }

    // MARK: - Aspect ratio helpers for trading cards
    private func expandToCardAspect(_ rect: CGRect) -> CGRect {
        let cardAspect: CGFloat = 2.5 / 3.5 // Standard trading card ratio ≈ 0.714
        let currentAspect = rect.width / rect.height

        var newRect = rect

        if currentAspect > cardAspect {
            // Too wide → expand height
            let newHeight = rect.width / cardAspect
            let delta = newHeight - rect.height
            newRect.origin.y -= delta / 2
            newRect.size.height = newHeight
        } else {
            // Too tall → expand width
            let newWidth = rect.height * cardAspect
            let delta = newWidth - rect.width
            newRect.origin.x -= delta / 2
            newRect.size.width = newWidth
        }

        return newRect
    }

    private func clampToBounds(_ rect: CGRect) -> CGRect {
        return CGRect(
            x: max(0, rect.origin.x),
            y: max(0, rect.origin.y),
            width: min(1 - rect.origin.x, rect.width),
            height: min(1 - rect.origin.y, rect.height)
        )
    }

    private func cropCapturedImage(_ image: UIImage, using normalizedRect: CGRect) -> UIImage {
        guard let cgImage = image.cgImage else { return image }

        let width = CGFloat(cgImage.width)
        let height = CGFloat(cgImage.height)

        // Expand to maintain trading card aspect ratio, then clamp to valid bounds
        let fitted = clampToBounds(expandToCardAspect(normalizedRect))

        // ⚠️ CRITICAL: Invert Y axis - metadataRect uses top-left origin, CGImage uses bottom-left
        let cropRect = CGRect(
            x: fitted.origin.x * width,
            y: (1 - fitted.origin.y - fitted.size.height) * height,
            width: fitted.size.width * width,
            height: fitted.size.height * height
        )

        print("📸 Image: \(Int(width))x\(Int(height))")
        print("📸 Fitted rect: (\(String(format: "%.3f", fitted.origin.x)), \(String(format: "%.3f", fitted.origin.y))) \(String(format: "%.3f", fitted.width))x\(String(format: "%.3f", fitted.height))")
        print("📸 Crop pixels (Y-inverted): (\(Int(cropRect.origin.x)), \(Int(cropRect.origin.y))) \(Int(cropRect.width))x\(Int(cropRect.height))")

        guard let croppedCG = cgImage.cropping(to: cropRect) else { return image }

        return UIImage(cgImage: croppedCG, scale: image.scale, orientation: image.imageOrientation)
    }
}

extension CameraPreviewView: AVCapturePhotoCaptureDelegate {
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        guard error == nil,
              let imageData = photo.fileDataRepresentation(),
              let image = UIImage(data: imageData) else {
            return
        }

        print("📸 Photo captured, running Vision detection...")

        // Use Vision to detect actual card edges (production-grade)
        VisionCardDetector.detectCard(in: image) { [weak self] result in
            guard let self = self else { return }

            let finalImage: UIImage

            if let visionResult = result {
                // ✅ Vision detected the card - crop to actual card edges
                print("✅ Using Vision-detected crop")
                finalImage = VisionCardDetector.cropToCard(image: image, result: visionResult)
            } else {
                // ⚠️ Vision failed - fall back to overlay-based crop
                print("⚠️ Vision failed, using overlay fallback")
                let normalizedRect = self.metadataRect(for: self.targetBoxFrame)
                finalImage = self.cropCapturedImage(image, using: normalizedRect)
            }

            // Check for blur before accepting the image
            let (isBlurry, sharpness) = BlurDetector.detectBlur(in: finalImage)

            DispatchQueue.main.async {
                if isBlurry {
                    // Reject blurry image - notify delegate to show retry message
                    print("❌ Image rejected: too blurry (sharpness: \(String(format: "%.1f", sharpness)))")
                    self.delegate?.didRejectBlurryImage(sharpness: sharpness)
                } else {
                    // Accept sharp image
                    print("✅ Image accepted (sharpness: \(String(format: "%.1f", sharpness)))")
                    self.delegate?.didCaptureImage(finalImage)
                }
            }
        }
    }
}

#Preview {
    CameraScannerView(viewModel: CardScannerViewModel())
        .preferredColorScheme(.dark)
}
