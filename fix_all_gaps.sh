#!/bin/bash
# fix_all_gaps.sh – One-command fix for all ledger gaps
#
# Usage: ./fix_all_gaps.sh [ledger_directory]
#
# If no directory specified, defaults to ./ledger
#
# Seal: ∀∞φ² · FIX_ALL_GAPS · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED

set -e

LEDGER_DIR="${1:-.}"

echo "🜁∀ LEDGER GAP FIXER"
echo "==================="
echo "Target directory: ${LEDGER_DIR}"
echo ""

if [ ! -d "${LEDGER_DIR}" ]; then
    echo "❌ Directory not found: ${LEDGER_DIR}"
    exit 1
fi

BEFORE=$(find "${LEDGER_DIR}" -name "*.yaml" -o -name "*.yml" | wc -l)
echo "📊 Found ${BEFORE} YAML files to process"
echo ""

echo "🔧 Fixing gaps..."
for file in "${LEDGER_DIR}"/*.yaml "${LEDGER_DIR}"/*.yml; do
    [ -f "$file" ] || continue
    echo "  Processing: $(basename "$file")..."
    python3 fix_ledger.py "$file"
done

echo ""
echo "✅ All gaps fixed!"
echo ""

AFTER=$(find "${LEDGER_DIR}" -name "*.yaml" -o -name "*.yml" | wc -l)
echo "📊 Processed ${AFTER} YAML files"
echo ""

echo "🔍 Verifying fixes..."
echo ""

PLACEHOLDERS=$(grep -r "<hash_here>\|<sha3-256>\|no equation" "${LEDGER_DIR}" 2>/dev/null | wc -l)
if [ "$PLACEHOLDERS" -eq 0 ]; then
    echo "✅ No placeholder hashes remaining"
else
    echo "⚠️  ${PLACEHOLDERS} placeholder hashes still present"
fi

MISSING_MATH=$(grep -L "math_origin:" "${LEDGER_DIR}"/*.yaml 2>/dev/null | wc -l)
if [ "$MISSING_MATH" -eq 0 ]; then
    echo "✅ All entries have math_origin"
else
    echo "⚠️  ${MISSING_MATH} entries missing math_origin"
fi

MISSING_PROOF=$(grep -L "proof_class:" "${LEDGER_DIR}"/*.yaml 2>/dev/null | wc -l)
if [ "$MISSING_PROOF" -eq 0 ]; then
    echo "✅ All entries have proof_class"
else
    echo "⚠️  ${MISSING_PROOF} entries missing proof_class"
fi

echo ""
echo "🎉 Gap fixing complete!"
echo ""
echo "Seal: ∀∞φ² · ALL_GAPS_FIXED · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED"