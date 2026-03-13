# =============================================================================
# AyushBot Backend — API Route: Sync Endpoints
# =============================================================================
#
# PURPOSE:
#   Handles data synchronization between ASHA Android phones and the PHC
#   gateway. When an ASHA arrives at the PHC with her phone, these endpoints
#   manage the bidirectional data exchange over the local Wi-Fi network.
#
# ENDPOINTS:
#
#   POST /api/v1/sync/upload
#     ASHA phone → Gateway: Upload offline encounter data.
#     When ASHAs collect data in the field without gateway connectivity,
#     the Android app stores encounters locally. When the ASHA returns to
#     the PHC, this endpoint receives the queued data.
#     - Request body: list of PatientAssessment objects + BLE sensor readings
#     - Response: count of accepted records + list of any rejected records
#       (with rejection reasons)
#     - Deduplication: If the same encounter_id already exists, skip it
#
#   GET /api/v1/sync/download
#     Gateway → ASHA phone: Download updated models and reference data.
#     - Returns a manifest of available updates:
#       - model_updates: list of updated model files with version + checksum
#       - reference_data: updated drug formulary, facility list, etc.
#       - asha_messages: administrative messages from the PHC Medical Officer
#     - The Android app downloads individual files via separate GET calls
#
#   GET /api/v1/sync/download/{resource_id}
#     Download a specific resource file (model binary, reference data file).
#     - Streams the file with Content-Length and checksum headers
#     - Supports range requests for resumable downloads
#
#   POST /api/v1/sync/feedback
#     Upload outcome feedback from the PHC Medical Officer.
#     After a referred patient is seen by the doctor, the doctor can provide
#     feedback on the triage accuracy (confirmed/modified diagnosis). This
#     feedback replaces pseudo-labels in the FL training pipeline.
#     - Request body: encounter_id + confirmed_diagnosis + doctor_notes
#
# SYNC PROTOCOL:
#   The Android app discovers the gateway via mDNS on the local network.
#   Sync is initiated by the phone, not the gateway. The phone first
#   uploads pending data, then checks for available downloads.
#
# CONFLICT RESOLUTION:
#   If the same patient has data from both offline phone storage and a
#   previous gateway sync, the NEWER timestamp wins. Conflicts are logged
#   for manual review by the Medical Officer.
# =============================================================================
