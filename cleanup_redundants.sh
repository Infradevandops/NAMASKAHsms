#!/bin/bash
# Redundant Files Cleanup - Minimal Implementation

set -e

echo "🧹 REDUNDANT FILES CLEANUP"
echo "This will archive redundant status/progress files"
echo ""

# Create archive directory
mkdir -p archive/redundant-docs-2026/

# Move redundant status files from docs/
echo "📁 Archiving redundant documentation..."

# Payment hardening redundant files
mv docs/payment-hardening/PAYMENT_HARDENING_COMPLETE.md archive/redundant-docs-2026/ 2>/dev/null || true
mv docs/payment-hardening/PAYMENT_HARDENING_PHASES_COMPLETE.md archive/redundant-docs-2026/ 2>/dev/null || true
mv docs/payment-hardening/PAYMENT_HARDENING_PROGRESS.md archive/redundant-docs-2026/ 2>/dev/null || true

# Checklist redundant files
mv docs/CHECKLIST_STATUS_SUMMARY.md archive/redundant-docs-2026/ 2>/dev/null || true
mv docs/FINAL_CHECKLIST_STATUS_COMPLETE.md archive/redundant-docs-2026/ 2>/dev/null || true
mv docs/CHECKLIST_COMPLETION_FINAL.md archive/redundant-docs-2026/ 2>/dev/null || true

# Roadmap redundant files
mv docs/roadmaps/Q1_2026_COMPLETE_ROADMAP.md archive/redundant-docs-2026/ 2>/dev/null || true

# Remove empty directories
rmdir docs/payment-hardening/ 2>/dev/null || true
rmdir docs/roadmaps/ 2>/dev/null || true

echo "✅ Redundant files archived to archive/redundant-docs-2026/"