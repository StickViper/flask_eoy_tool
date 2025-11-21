"""
Test CMS PECOS API access and query capabilities
Tests filtering, pagination, and NPI lookups
"""

import requests
import json
from time import sleep

# PECOS dataset endpoint
BASE_URL = "https://data.cms.gov/data-api/v1/dataset/2457ea29-fc82-48b0-86ec-3b0755de7515/data"


def test_basic_query():
    """Test 1: Basic query - get first 10 records"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Query (first 10 records)")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}?size=10")
        response.raise_for_status()
        data = response.json()

        print(f"✅ Status: {response.status_code}")
        print(f"✅ Records returned: {len(data)}")

        if len(data) > 0:
            print(f"\n📋 First record fields:")
            for key in data[0].keys():
                value = data[0][key]
                # Truncate long values
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
                print(f"   {key}: {display_value}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        return False


def test_filter_by_state():
    """Test 2: Filter by state code"""
    print("\n" + "=" * 60)
    print("TEST 2: Filter by State (TX)")
    print("=" * 60)

    # Try different filter syntaxes (common REST patterns)
    filter_attempts = [
        ("?filter[STATE_CD]=TX&size=5", "Bracket notation"),
        ("?STATE_CD=TX&size=5", "Direct param"),
        ("?filter=STATE_CD:TX&size=5", "Colon notation"),
    ]

    for params, description in filter_attempts:
        print(f"\n🧪 Trying {description}: {params}")
        try:
            response = requests.get(BASE_URL + params)
            response.raise_for_status()
            data = response.json()

            if len(data) > 0:
                # Check if filtering worked
                states = [r.get('STATE_CD', 'N/A') for r in data[:5]]
                print(f"✅ Got {len(data)} records, states: {states}")

                if all(s == 'TX' for s in states if s != 'N/A'):
                    print(f"✅ Filtering works with {description}!")
                    return params  # Return working syntax
                else:
                    print(f"⚠️  Filtering didn't work (got mixed states)")
            else:
                print(f"⚠️  No records returned")

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed: {e}")

    print("\n⚠️  Could not determine state filter syntax")
    return None


def test_filter_by_npi():
    """Test 3: Filter by specific NPI"""
    print("\n" + "=" * 60)
    print("TEST 3: Filter by NPI")
    print("=" * 60)

    # First, get a valid NPI from the dataset
    print("\n📥 Fetching sample NPI...")
    try:
        response = requests.get(f"{BASE_URL}?size=1")
        response.raise_for_status()
        data = response.json()

        if len(data) == 0:
            print("❌ No data returned")
            return False

        sample_npi = data[0].get('NPI', None)
        if not sample_npi:
            print("❌ No NPI field found in data")
            return False

        print(f"✅ Sample NPI: {sample_npi}")

    except Exception as e:
        print(f"❌ Failed to get sample NPI: {e}")
        return False

    # Try to filter by that NPI
    print(f"\n🔍 Filtering by NPI: {sample_npi}")

    filter_attempts = [
        (f"?filter[NPI]={sample_npi}", "Bracket notation"),
        (f"?NPI={sample_npi}", "Direct param"),
        (f"?filter=NPI:{sample_npi}", "Colon notation"),
    ]

    for params, description in filter_attempts:
        print(f"\n🧪 Trying {description}")
        try:
            response = requests.get(BASE_URL + params)
            response.raise_for_status()
            data = response.json()

            if len(data) > 0 and data[0].get('NPI') == sample_npi:
                print(f"✅ Filtering works with {description}!")
                print(f"   Found: {data[0].get('FIRST_NAME')} {data[0].get('LAST_NAME')} ({data[0].get('STATE_CD')})")
                return params
            else:
                print(f"⚠️  No exact match")

        except Exception as e:
            print(f"❌ Failed: {e}")

    print("\n⚠️  Could not determine NPI filter syntax")
    return None


def test_pagination():
    """Test 4: Pagination"""
    print("\n" + "=" * 60)
    print("TEST 4: Pagination")
    print("=" * 60)

    pagination_attempts = [
        ("?size=5&offset=0", "First page"),
        ("?size=5&offset=5", "Second page (offset)"),
        ("?limit=5&skip=5", "Second page (limit/skip)"),
    ]

    first_page_npis = []

    for params, description in pagination_attempts:
        print(f"\n🧪 Testing {description}: {params}")
        try:
            response = requests.get(BASE_URL + params)
            response.raise_for_status()
            data = response.json()

            if len(data) > 0:
                npis = [r.get('NPI') for r in data[:5]]
                print(f"✅ Got {len(data)} records")
                print(f"   NPIs: {npis[:3]}...")

                if description == "First page":
                    first_page_npis = npis
                elif first_page_npis:
                    # Check if second page has different NPIs
                    overlap = set(first_page_npis) & set(npis)
                    if len(overlap) == 0:
                        print(f"✅ Pagination works! No overlap with first page.")
                    else:
                        print(f"⚠️  {len(overlap)} overlapping records")

        except Exception as e:
            print(f"❌ Failed: {e}")

    return True


def test_bulk_npi_lookup():
    """Test 5: Bulk NPI lookup performance"""
    print("\n" + "=" * 60)
    print("TEST 5: Bulk NPI Lookup Performance")
    print("=" * 60)

    # Get 100 random NPIs to test batch query performance
    print("\n📥 Fetching 100 NPIs for performance test...")
    try:
        response = requests.get(f"{BASE_URL}?size=100")
        response.raise_for_status()
        data = response.json()
        test_npis = [r.get('NPI') for r in data if r.get('NPI')][:10]  # Test with 10

        print(f"✅ Got {len(test_npis)} NPIs to test")

        # Method 1: Individual queries
        print(f"\n⏱️  Method 1: Individual queries (sequential)")
        import time
        start = time.time()
        successful = 0

        for npi in test_npis[:5]:  # Test first 5
            try:
                resp = requests.get(f"{BASE_URL}?NPI={npi}&size=1", timeout=5)
                if resp.status_code == 200:
                    successful += 1
            except:
                pass

        elapsed = time.time() - start
        print(f"   ✅ {successful}/5 successful in {elapsed:.2f}s ({elapsed/5:.2f}s per NPI)")

        # Method 2: Bulk query (if API supports IN operator)
        print(f"\n⏱️  Method 2: Bulk query (if supported)")
        print(f"   ℹ️  Testing if API supports IN/OR operators...")

        # Try comma-separated
        npi_list = ",".join(test_npis[:5])
        try:
            resp = requests.get(f"{BASE_URL}?NPI={npi_list}&size=5", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1:
                    print(f"   ✅ Bulk query works! Got {len(data)} records in one request")
                else:
                    print(f"   ⚠️  Bulk query not supported (single record returned)")
        except Exception as e:
            print(f"   ⚠️  Bulk query not supported: {e}")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_response_structure():
    """Test 6: Analyze response structure for PECOS filtering"""
    print("\n" + "=" * 60)
    print("TEST 6: Response Structure Analysis")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}?size=50")
        response.raise_for_status()
        data = response.json()

        print(f"✅ Got {len(data)} records\n")

        # Analyze provider types
        print("📊 Provider Types Distribution:")
        provider_types = {}
        for record in data:
            ptype = record.get('PROVIDER_TYPE_DESC', 'Unknown')
            provider_types[ptype] = provider_types.get(ptype, 0) + 1

        for ptype, count in sorted(provider_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ptype}: {count}")

        # Analyze states
        print("\n📊 State Distribution:")
        states = {}
        for record in data:
            state = record.get('STATE_CD', 'Unknown')
            states[state] = states.get(state, 0) + 1

        for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {state}: {count}")

        # Check for enrollment status field
        print("\n🔍 Checking for enrollment status indicators:")
        sample_record = data[0]
        status_fields = [k for k in sample_record.keys() if 'status' in k.lower() or 'enroll' in k.lower()]
        if status_fields:
            print(f"   ✅ Found status fields: {status_fields}")
            for field in status_fields:
                print(f"      {field}: {sample_record[field]}")
        else:
            print(f"   ℹ️  No obvious status field (all records may be active)")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """Run all PECOS API tests"""
    print("=" * 60)
    print("CMS PECOS API TEST SUITE")
    print("=" * 60)
    print("""
This script tests the CMS PECOS Medicare enrollment API.
Goal: Determine how to query and filter provider data.

Dataset: Provider Enrollment, Chain, and Ownership System (PECOS)
URL: https://data.cms.gov/data-api/v1/dataset/2457ea29-fc82-48b0-86ec-3b0755de7515/data
""")

    results = {
        "Basic Query": test_basic_query(),
        "State Filter": test_filter_by_state() is not None,
        "NPI Filter": test_filter_by_npi() is not None,
        "Pagination": test_pagination(),
        "Bulk Lookup": test_bulk_npi_lookup(),
        "Response Structure": test_response_structure(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! PECOS API is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check output above for details.")

    print("\n📝 Next step: Build pecos_cross_reference.py using working query syntax")


if __name__ == '__main__':
    main()
