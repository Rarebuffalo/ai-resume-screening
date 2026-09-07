from unittest.mock import patch, MagicMock
from github_client import enrich_github_profile

def test_missing_github_does_not_fail():
    res = enrich_github_profile(None)
    assert res.total_score == 0
    assert res.status == "skipped"

def test_github_404_not_found_handled():
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        res = enrich_github_profile("nonexistent_user_99999")
        assert res.total_score == 0
        assert res.status == "not_found"

def test_github_403_rate_limit_handled():
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_get.return_value = mock_resp

        res = enrich_github_profile("rate_limited_user_1234")
        assert res.total_score == 0
        assert res.status == "rate_limited"
        assert "rate limit" in res.summary.lower()

def test_github_network_timeout_does_not_crash():
    with patch("requests.get", side_effect=Exception("Connection timed out")):
        res = enrich_github_profile("timeout_user_5678")
        assert res.total_score == 0
        assert res.status == "error"
