"""
Test corrected ATH phase detection logic
"""
import sys
sys.path.insert(0, '.')

from app.services.ath_analyzer import ATHAnalyzer

# Create analyzer instance
analyzer = ATHAnalyzer()

# Test the _determine_phase_and_status method directly
print("="*60)
print("TESTING CORRECTED PHASE LOGIC")
print("="*60)

test_cases = [
    {
        "name": "Test Case 1: Phase 1 (At ATH)",
        "ath": 100,
        "price": 99.5,
        "ema": 90,
        "expected_phase": 1,
        "expected_label": "Phase 1 (At ATH)"
    },
    {
        "name": "Test Case 2: Phase 1 (New ATH)",
        "ath": 100,
        "price": 105,
        "ema": 95,
        "expected_phase": 1,
        "expected_label": "Phase 1 (At ATH)"
    },
    {
        "name": "Test Case 3: Phase 2 (Consolidation)",
        "ath": 100,
        "price": 85,
        "ema": 90,
        "expected_phase": 2,
        "expected_label": "Phase 2 (Consolidation)"
    },
    {
        "name": "Test Case 4: Phase 3 (Entry Setup)",
        "ath": 100,
        "price": 92,
        "ema": 88,
        "expected_phase": 3,
        "expected_label": "Phase 3 (Entry Setup)"
    },
    {
        "name": "Test Case 5: Phase 3 (Edge Case)",
        "ath": 100,
        "price": 97.5,
        "ema": 90,
        "expected_phase": 3,
        "expected_label": "Phase 3 (Entry Setup)"
    }
]

passed = 0
failed = 0

for test in test_cases:
    print(f"\n{test['name']}")
    print(f"  ATH: {test['ath']}, Price: {test['price']}, EMA 200: {test['ema']}")

    phase, label = analyzer._determine_phase_and_status(
        test['price'],
        test['ema'],
        test['ath']
    )

    distance = ((test['price'] - test['ath']) / test['ath']) * 100

    print(f"  Distance from ATH: {distance:.1f}%")
    print(f"  Result: Phase {phase} - {label}")
    print(f"  Expected: Phase {test['expected_phase']} - {test['expected_label']}")

    if phase == test['expected_phase'] and label == test['expected_label']:
        print("  [PASS]")
        passed += 1
    else:
        print("  [FAIL]")
        failed += 1

print("\n" + "="*60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*60)

if failed == 0:
    print("\n[OK] All tests passed! Phase logic is correct.")
else:
    print(f"\n[ERROR] {failed} test(s) failed. Phase logic needs review.")

# Test with real data
print("\n" + "="*60)
print("TESTING WITH REAL DATA (if available)")
print("="*60)

test_symbols = ['RELIANCE', 'TCS', 'INFY']
for symbol in test_symbols:
    result = analyzer.analyze_symbol(symbol)
    if result:
        print(f"\n{symbol}:")
        print(f"  Phase {result['phase']} - {result['status_label']}")
        print(f"  ATH: {result['ath_value']:.2f} (on {result['ath_date']})")
        print(f"  Current: {result['current_price']:.2f}")
        print(f"  EMA 200: {result['ema_200']:.2f}")
        print(f"  Distance from ATH: {result['distance_from_ath']:.1f}%")
    else:
        print(f"\n{symbol}: No data available")
