from backend.core.auth import create_api_key, list_api_keys


def test_create_api_key_with_tier():
    ak = create_api_key(owner='tiered', tier='CREATOR')
    assert ak.tier == 'CREATOR'

    keys = list_api_keys()
    found = [k for k in keys if k.key == ak.key]
    assert found and found[0].tier == 'CREATOR'
