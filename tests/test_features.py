from backend.core.features import tier_has, tier_limit


def test_feature_matrix_download():
    assert tier_has('can_download_audio', 'FREE') is False
    assert tier_has('can_download_audio', 'CREATOR') is True
    assert tier_has('can_download_audio', 'PRO') is True


def test_limits():
    assert tier_limit('max_jobs_per_month', 'FREE') == 10
    assert tier_limit('max_jobs_per_month', 'CREATOR') == 500
    assert tier_limit('max_jobs_per_month', 'PRO') == 5000
