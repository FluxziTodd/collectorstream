import SwiftUI

struct ScanCardView: View {
    @StateObject private var scannerViewModel = CardScannerViewModel()
    @EnvironmentObject var cardStore: CardStore
    @Binding var selectedTab: Int

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    TopAccentBar()

                    switch scannerViewModel.scanState {
                    case .ready:
                        ReadyToScanView(viewModel: scannerViewModel)
                    case .scanning:
                        CameraScannerView(viewModel: scannerViewModel)
                    case .reviewFront:
                        ReviewImageView(
                            viewModel: scannerViewModel,
                            side: "front",
                            title: "Front of Card",
                            onContinue: { scannerViewModel.proceedToBack() },
                            onRetake: { scannerViewModel.retakeFront() }
                        )
                    case .scanningBack:
                        CameraScannerView(viewModel: scannerViewModel)
                    case .reviewBack:
                        ReviewImageView(
                            viewModel: scannerViewModel,
                            side: "back",
                            title: "Back of Card",
                            onContinue: { Task { await scannerViewModel.processCard() } },
                            onRetake: { scannerViewModel.retakeBack() }
                        )
                    case .processing:
                        ProcessingView(message: "Identifying card...")
                    case .identified:
                        CardIdentifiedView(viewModel: scannerViewModel, cardStore: cardStore, selectedTab: $selectedTab)
                    case .error(let message):
                        ErrorStateView(
                            message: message,
                            onRetry: { scannerViewModel.reset() }
                        )
                    }
                }
            }
            .navigationTitle("Scan Card")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if scannerViewModel.scanState != .ready {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("Cancel") {
                            scannerViewModel.reset()
                        }
                        .foregroundColor(Theme.Colors.accent)
                    }
                }
            }
        }
    }
}

// MARK: - Ready to Scan View
struct ReadyToScanView: View {
    @ObservedObject var viewModel: CardScannerViewModel

    var body: some View {
        VStack(spacing: Theme.Spacing.xl) {
            Spacer()

            // Icon
            ZStack {
                Circle()
                    .fill(Theme.Colors.bgCard)
                    .frame(width: 120, height: 120)

                Image(systemName: "camera.viewfinder")
                    .font(.system(size: 48))
                    .foregroundColor(Theme.Colors.accent)
            }

            // Instructions
            VStack(spacing: Theme.Spacing.sm) {
                Text("Scan Your Card")
                    .font(Theme.Typography.title2)
                    .foregroundColor(Theme.Colors.textPrimary)

                Text("Position your card within the frame.\nWe'll capture the front and back.")
                    .font(Theme.Typography.body)
                    .foregroundColor(Theme.Colors.textSecondary)
                    .multilineTextAlignment(.center)
            }

            Spacer()

            // Tips
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                TipRow(icon: "lightbulb", text: "Use good lighting")
                TipRow(icon: "rectangle.portrait", text: "Keep card flat and centered")
                TipRow(icon: "hand.raised", text: "Hold steady while scanning")
            }
            .padding(Theme.Spacing.lg)
            .background(Theme.Colors.bgCard)
            .cornerRadius(Theme.CornerRadius.medium)
            .overlay(
                RoundedRectangle(cornerRadius: Theme.CornerRadius.medium)
                    .stroke(Theme.Colors.border, lineWidth: 1)
            )
            .padding(.horizontal, Theme.Spacing.lg)

            Spacer()

            // Scan Button
            PrimaryButton(title: "Start Scanning", action: {
                viewModel.startScanning()
            })
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.bottom, Theme.Spacing.xl)
        }
    }
}

struct TipRow: View {
    let icon: String
    let text: String

    var body: some View {
        HStack(spacing: Theme.Spacing.md) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(Theme.Colors.accent)
                .frame(width: 24)

            Text(text)
                .font(Theme.Typography.subheadline)
                .foregroundColor(Theme.Colors.textSecondary)
        }
    }
}

// MARK: - Review Image View
struct ReviewImageView: View {
    @ObservedObject var viewModel: CardScannerViewModel
    let side: String
    let title: String
    let onContinue: () -> Void
    let onRetake: () -> Void

    var image: UIImage? {
        side == "front" ? viewModel.frontImage : viewModel.backImage
    }

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Text(title)
                .font(Theme.Typography.title3)
                .foregroundColor(Theme.Colors.textPrimary)
                .padding(.top, Theme.Spacing.lg)

            if let image = image {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(maxHeight: 400)
                    .cornerRadius(Theme.CornerRadius.medium)
                    .overlay(
                        RoundedRectangle(cornerRadius: Theme.CornerRadius.medium)
                            .stroke(Theme.Colors.accent, lineWidth: 2)
                    )
                    .padding(.horizontal, Theme.Spacing.lg)
            }

            Text("Does this look good?")
                .font(Theme.Typography.subheadline)
                .foregroundColor(Theme.Colors.textSecondary)

            Spacer()

            HStack(spacing: Theme.Spacing.md) {
                SecondaryButton(title: "Retake", action: onRetake)
                PrimaryButton(
                    title: side == "front" ? "Scan Back" : "Identify Card",
                    action: onContinue
                )
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.bottom, Theme.Spacing.xl)
        }
    }
}

// MARK: - Processing View
struct ProcessingView: View {
    let message: String

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Spacer()

            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: Theme.Colors.accent))
                .scaleEffect(2)

            Text(message)
                .font(Theme.Typography.headline)
                .foregroundColor(Theme.Colors.textPrimary)

            Text("This may take a moment...")
                .font(Theme.Typography.subheadline)
                .foregroundColor(Theme.Colors.textSecondary)

            Spacer()
        }
    }
}

// MARK: - Card Identified View
struct CardIdentifiedView: View {
    @ObservedObject var viewModel: CardScannerViewModel
    @ObservedObject var cardStore: CardStore
    @Binding var selectedTab: Int
    @Environment(\.dismiss) var dismiss

    @State private var isSaving = false
    @State private var showSuccess = false
    @State private var showError = false
    @State private var errorMessage = ""

    var body: some View {
        ScrollView {
            VStack(spacing: Theme.Spacing.lg) {
                // Success Icon
                ZStack {
                    Circle()
                        .fill(Theme.Colors.success.opacity(0.2))
                        .frame(width: 80, height: 80)

                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 48))
                        .foregroundColor(Theme.Colors.success)
                }
                .padding(.top, Theme.Spacing.lg)

                Text("Card Identified!")
                    .font(Theme.Typography.title2)
                    .foregroundColor(Theme.Colors.textPrimary)

                // Card Preview
                HStack(spacing: Theme.Spacing.md) {
                    if let front = viewModel.frontImage {
                        Image(uiImage: front)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(height: 150)
                            .cornerRadius(Theme.CornerRadius.small)
                    }

                    if let back = viewModel.backImage {
                        Image(uiImage: back)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(height: 150)
                            .cornerRadius(Theme.CornerRadius.small)
                    }
                }
                .padding(.horizontal, Theme.Spacing.lg)

                // Identified Info
                if let identification = viewModel.identification {
                    CardInfoForm(viewModel: viewModel)
                }

                // Confidence Score
                if let confidence = viewModel.identification?.confidence {
                    HStack {
                        Image(systemName: "sparkles")
                            .foregroundColor(Theme.Colors.accent)
                        Text("AI Confidence: \(Int(confidence * 100))%")
                            .font(Theme.Typography.footnote)
                            .foregroundColor(Theme.Colors.textSecondary)
                    }
                }

                Spacer()

                // Actions
                VStack(spacing: Theme.Spacing.md) {
                    PrimaryButton(
                        title: "Add to Collection",
                        action: {
                            Task {
                                await saveCard()
                            }
                        },
                        isLoading: isSaving
                    )

                    SecondaryButton(title: "Scan Another", action: {
                        viewModel.reset()
                    })
                }
                .padding(.horizontal, Theme.Spacing.lg)
                .padding(.bottom, Theme.Spacing.xl)
            }
        }
        .alert("Card Added!", isPresented: $showSuccess) {
            Button("Scan Another") {
                viewModel.reset()
            }
            Button("View Collection") {
                viewModel.reset()
                selectedTab = 0  // Switch to Collection tab
            }
        } message: {
            Text("Your card has been added to your collection.")
        }
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(errorMessage)
        }
    }

    private func saveCard() async {
        isSaving = true
        print("💾 Starting card save process...")

        // Upload images first to get URLs
        var frontImageUrl: String?
        var backImageUrl: String?

        do {
            // Upload front image
            if let frontImage = viewModel.frontImage {
                print("📤 Uploading front image...")
                guard let frontData = frontImage.jpegData(compressionQuality: 0.95) else {
                    throw NSError(domain: "CardSave", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to convert front image to JPEG"])
                }
                let frontResponse = try await APIClient.shared.uploadImage(frontData, side: "front")
                frontImageUrl = frontResponse.url
                print("✅ Front image uploaded: \(frontImageUrl ?? "nil")")
            } else {
                print("⚠️ No front image to upload")
            }

            // Upload back image (if exists)
            if let backImage = viewModel.backImage {
                print("📤 Uploading back image...")
                guard let backData = backImage.jpegData(compressionQuality: 0.95) else {
                    throw NSError(domain: "CardSave", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to convert back image to JPEG"])
                }
                let backResponse = try await APIClient.shared.uploadImage(backData, side: "back")
                backImageUrl = backResponse.url
                print("✅ Back image uploaded: \(backImageUrl ?? "nil")")
            } else {
                print("ℹ️ No back image to upload")
            }

            // Create card upload with image URLs
            print("💾 Creating card with URLs - Front: \(frontImageUrl ?? "nil"), Back: \(backImageUrl ?? "nil")")
            print("💰 Estimated value: \(viewModel.identification?.estimatedValue ?? 0)")
            print("🏀 Sport: \(viewModel.editableSport.rawValue)")
            let cardUpload = CardUpload(
                playerName: viewModel.editablePlayerName,
                team: viewModel.editableTeam,
                year: viewModel.editableYear,
                set: viewModel.editableSet,
                cardNumber: viewModel.editableCardNumber,
                manufacturer: viewModel.identification?.manufacturer,
                sport: viewModel.editableSport,
                condition: viewModel.editableCondition,
                gradingCompany: viewModel.identification?.grading?.company,
                gradingGrade: viewModel.identification?.grading?.grade,
                gradingCertNumber: viewModel.identification?.grading?.certNumber,
                frontImageUrl: frontImageUrl,
                backImageUrl: backImageUrl,
                estimatedValue: viewModel.identification?.estimatedValue,
                purchasePrice: viewModel.editablePurchasePrice,
                notes: nil
            )

            // Save card to collection
            print("💾 Saving card to collection...")
            if let savedCard = await cardStore.addCard(cardUpload) {
                print("✅ Card saved successfully! ID: \(savedCard.id)")
                showSuccess = true
            } else {
                print("❌ Failed to save card - addCard returned nil")
                errorMessage = cardStore.errorMessage ?? "Failed to save card to collection"
                showError = true
            }
        } catch {
            print("❌ Error saving card: \(error.localizedDescription)")
            errorMessage = "Failed to save card: \(error.localizedDescription)"
            showError = true
        }

        isSaving = false
    }
}

// MARK: - Card Info Form
struct CardInfoForm: View {
    @ObservedObject var viewModel: CardScannerViewModel

    var body: some View {
        VStack(spacing: Theme.Spacing.md) {
            // Player Name
            VStack(alignment: .leading, spacing: 4) {
                Text("Player Name")
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textSecondary)
                ThemedTextField(placeholder: "Player Name", text: $viewModel.editablePlayerName)
            }

            // Team
            VStack(alignment: .leading, spacing: 4) {
                Text("Team")
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textSecondary)
                ThemedTextField(placeholder: "Team", text: $viewModel.editableTeam)
            }

            // Year & Card Number
            HStack(spacing: Theme.Spacing.md) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Year")
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                    ThemedTextField(placeholder: "Year", text: $viewModel.editableYear)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Card #")
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                    ThemedTextField(placeholder: "Card #", text: $viewModel.editableCardNumber)
                }
            }

            // Set
            VStack(alignment: .leading, spacing: 4) {
                Text("Set")
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textSecondary)
                ThemedTextField(placeholder: "Set", text: $viewModel.editableSet)
            }

            // Sport Picker
            VStack(alignment: .leading, spacing: 4) {
                Text("Sport")
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textSecondary)
                Picker("Sport", selection: $viewModel.editableSport) {
                    ForEach(Card.Sport.allCases, id: \.self) { sport in
                        Text(sport.displayName).tag(sport)
                    }
                }
                .pickerStyle(.segmented)
            }

            // Estimated Value
            if let value = viewModel.identification?.estimatedValue {
                HStack {
                    Text("Estimated Value")
                        .font(Theme.Typography.subheadline)
                        .foregroundColor(Theme.Colors.textSecondary)
                    Spacer()
                    Text("$\(Int(value))")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.success)
                }
                .padding()
                .background(Theme.Colors.bgCard)
                .cornerRadius(Theme.CornerRadius.medium)
            }
        }
        .padding(.horizontal, Theme.Spacing.lg)
    }
}

// MARK: - Error State View
struct ErrorStateView: View {
    let message: String
    let onRetry: () -> Void

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Spacer()

            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 64))
                .foregroundColor(Theme.Colors.warning)

            Text("Something went wrong")
                .font(Theme.Typography.title2)
                .foregroundColor(Theme.Colors.textPrimary)

            Text(message)
                .font(Theme.Typography.body)
                .foregroundColor(Theme.Colors.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, Theme.Spacing.xl)

            Spacer()

            PrimaryButton(title: "Try Again", action: onRetry)
                .padding(.horizontal, Theme.Spacing.lg)
                .padding(.bottom, Theme.Spacing.xl)
        }
    }
}

#Preview {
    struct PreviewWrapper: View {
        @State var selectedTab = 1
        var body: some View {
            ScanCardView(selectedTab: $selectedTab)
                .environmentObject(CardStore())
                .preferredColorScheme(.dark)
        }
    }
    return PreviewWrapper()
}
