#!/bin/bash
# Quick test script to verify all demo recipes work

echo "🧪 Testing mtop Demo Framework"
echo "================================"

cd "$(dirname "$0")"

# Test demo script listing
echo "📋 Testing demo listing..."
python3 scripts/demo.py --list > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Demo listing works"
else
    echo "❌ Demo listing failed"
    exit 1
fi

# Test each demo recipe in dry-run mode
recipes=("startup" "enterprise" "canary-failure" "cost-optimization" "research-lab")

for recipe in "${recipes[@]}"; do
    echo "🧪 Testing $recipe recipe..."
    python3 scripts/demo.py "$recipe" --dry-run > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ $recipe recipe works"
    else
        echo "❌ $recipe recipe failed"
        exit 1
    fi
done

# Test config mixer help
echo "🎛️ Testing config mixer..."
python3 scripts/config-mixer.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Config mixer works"
else
    echo "❌ Config mixer failed"
    exit 1
fi

# Test basic mtop functionality
echo "🚀 Testing basic mtop..."
python3 mtop-main list > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Basic mtop works"
else
    echo "❌ Basic mtop failed"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Demo framework is ready to use."
echo ""
echo "Try these commands:"
echo "  ./scripts/demo.py --list"
echo "  ./scripts/demo.py startup --dry-run"
echo "  ./scripts/config-mixer.py --quick"
echo ""