import pytest
import math
from app.services.area_code_geo import (
    NANPA_DATA,
    _haversine,
    get_metro_codes,
    filter_supported,
    get_nearby
)

def test_haversine_distance():
    # Test known distance
    # LA to NY is ~2445 miles
    la_lat, la_lng = 34.0522, -118.2437
    ny_lat, ny_lng = 40.7128, -74.0060
    dist = _haversine(la_lat, la_lng, ny_lat, ny_lng)
    
    assert 2400 < dist < 2500

def test_get_metro_codes():
    codes = get_metro_codes("213")
    # All LA codes should be returned
    assert "323" in codes
    assert "818" in codes
    assert "916" not in codes # Sacramento, different metro
    
    # Unknown code
    assert get_metro_codes("999") == []

def test_filter_supported():
    test_codes = ["213", "999", "323", "415"]
    
    # String format
    supported_list_strings = ["213", "323", "415", "916"]
    result1 = filter_supported(test_codes, supported_list_strings)
    assert "999" not in result1
    assert "213" in result1
    assert "323" in result1
    assert "415" in result1

    # Dict format as returned from TextVerified mock
    supported_list_dicts = [
        {"area_code": "213", "state": "CA"},
        {"area_code": "323", "state": "CA"},
        {"area_code": "415", "state": "CA"}
    ]
    result2 = filter_supported(test_codes, supported_list_dicts)
    assert "999" not in result2
    assert "213" in result2
    assert "323" in result2

def test_get_nearby():
    # Known LA code
    nearby = get_nearby("213")
    
    # Needs to return same_city (like 323, 310, 818) before same_state (916, 415)
    area_codes = [x["area_code"] for x in nearby]
    
    assert "323" in area_codes
    assert "310" in area_codes
    
    # Ensure same_city comes before same_state
    for i, item in enumerate(nearby):
        if item["area_code"] == "323":
            idx_323 = i
        if item["area_code"] == "916":
            idx_916 = i
    
    # It might not return 916 if max_results=8 is filled by other LA codes
    # Because there are 7 other LA codes in the list
    if "916" in area_codes:
        assert idx_323 < idx_916
        
    # Same state tests - Sacramento is in same state but should not be nearby because > 50mi
    # Let's verify for 916
    nearby_sac = get_nearby("916")
    prox_types = [x["proximity"] for x in nearby_sac if x["area_code"] != "279"]
    # All other CA codes returned should be same_state since they are >50mi from sacramento in this dataset.
    assert all(p == "same_state" for p in prox_types)
    
    # Test unknown code
    assert get_nearby("999") == []
