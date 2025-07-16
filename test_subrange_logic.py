#!/usr/bin/env python3
"""
Test Subrange Logic
Test the logic that determines when to skip subrange filtering
"""

def test_subrange_logic():
    """Test the subrange logic"""
    print("🔍 Testing Subrange Logic")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        ("Galaxy", "6000", "Galaxy 6000"),
        ("MiCOM", "P20", "MiCOM P20"),
        ("SEPAM", "20", "SEPAM 20"),
        ("PIX", "2B", "PIX 2B"),
    ]
    
    for range_label, subrange_label, expected_range in test_cases:
        print(f"\n📋 Test: range='{range_label}', subrange='{subrange_label}'")
        
        # Check if the range already includes the subrange
        range_includes_subrange = False
        if range_label and subrange_label:
            if subrange_label in range_label:
                range_includes_subrange = True
        
        print(f"  • Range includes subrange: {range_includes_subrange}")
        
        # Check if we should apply subrange filter
        should_apply_subrange = not range_includes_subrange
        print(f"  • Should apply subrange filter: {should_apply_subrange}")
        
        if should_apply_subrange:
            print(f"  • Would add subrange conditions for: {subrange_label}")
        else:
            print(f"  • Would SKIP subrange filter (range already includes it)")
        
        # Check what the actual range would be
        actual_range = f"{range_label} {subrange_label}" if range_label and subrange_label else range_label
        print(f"  • Actual range would be: '{actual_range}'")
        print(f"  • Expected range: '{expected_range}'")

if __name__ == "__main__":
    test_subrange_logic() 