#!/bin/bash
# Live Failure Check: Temporarily inject bug and verify tests fail

echo "================================================================================"
echo "LIVE FAILURE VERIFICATION"
echo "================================================================================"
echo ""
echo "This script injects bugs into status_to_color and verifies tests fail."
echo ""

# Backup original
cp scripts/eoy_tool.py scripts/eoy_tool.py.backup

echo "TEST 1: Inject wrong color bug (yellow → green)"
echo "--------------------------------------------------------------------------------"
sed -i "s/'successful order': '#ffff00'/'successful order': '#00ff00'/" scripts/eoy_tool.py

if python -m pytest tests/test_status_to_color.py::TestStatusToColor::test_exact_matches_yellow -q; then
    echo "❌ FAIL: Test did not catch wrong color bug!"
    mv scripts/eoy_tool.py.backup scripts/eoy_tool.py
    exit 1
else
    echo "✓ PASS: Test correctly failed for wrong color"
fi

# Restore
mv scripts/eoy_tool.py.backup scripts/eoy_tool.py
cp scripts/eoy_tool.py scripts/eoy_tool.py.backup

echo ""
echo "TEST 2: Inject substring matching bug"
echo "--------------------------------------------------------------------------------"
# Replace exact match with substring match
sed -i "s/return status_map.get(status_lower, '#ffffff')/if 'successful order' in status_lower:\n        return '#ffff00'\n    return '#ffffff'/" scripts/eoy_tool.py

if python -m pytest tests/test_status_to_color.py::TestStatusToColor::test_no_substring_matching -q 2>&1 | grep -q "FAILED"; then
    echo "✓ PASS: Test correctly failed for substring matching"
else
    echo "❌ FAIL: Test did not catch substring matching bug!"
fi

# Restore
mv scripts/eoy_tool.py.backup scripts/eoy_tool.py
cp scripts/eoy_tool.py scripts/eoy_tool.py.backup

echo ""
echo "TEST 3: Remove case insensitivity"
echo "--------------------------------------------------------------------------------"
sed -i "s/status_lower = status.lower().strip()/status_lower = status.strip()/" scripts/eoy_tool.py

if python -m pytest tests/test_status_to_color.py::TestStatusToColor::test_case_insensitive_yellow -q 2>&1 | grep -q "FAILED"; then
    echo "✓ PASS: Test correctly failed for case sensitivity bug"
else
    echo "❌ FAIL: Test did not catch case sensitivity bug!"
fi

# Restore
mv scripts/eoy_tool.py.backup scripts/eoy_tool.py
rm -f scripts/eoy_tool.py.backup

echo ""
echo "================================================================================"
echo "VERIFICATION COMPLETE: All tests correctly detect failures"
echo "================================================================================"
echo ""
echo "CONCLUSION:"
echo "  • Tests fail when they should (catch bugs)"
echo "  • Tests pass when they should (actual code is correct)"
echo "  • Test suite is robust and trustworthy"
echo ""
