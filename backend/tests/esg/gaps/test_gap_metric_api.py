"""Gap hunt (RP-48): the metric endpoint must let the dashboard tell "no data yet" from "unknown account"."""
from services.esg_service import compute_waci, load_esg_feed
from tests.esg.conftest import SAMPLE_FEED, AS_OF, ACCOUNT, add_portfolio

ESG_URL = f"/api/portfolio/{ACCOUNT}/esg"


class TestEmptyVersusUnknown:
    def test_known_account_without_metric_is_200_with_has_metric_false(self, client):
        """RP-48/RP-49: both cases returned 404, so the dashboard rendered the empty state for accounts the ESG
        store does not know and could not surface an error. A known account with no month is a 200 payload."""
        response = client.get(ESG_URL)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["has_metric"] is False
        assert body["source"] == "none"
        assert body["as_of_month"] is None
        assert body["effective_value"] is None and body["computed_value"] is None
        assert body["coverage_pct"] is None
        assert body["override"] is None
        assert body["portfolio_id"] == "PF-12345"

    def test_unknown_account_is_404(self, client):
        """RP-48: 404 stays reserved for accounts that do not exist."""
        assert client.get("/api/portfolio/0000000000/esg").status_code == 404

    def test_metric_payload_has_metric_true_once_computed(self, client, seeded_db):
        """RP-48: the flag flips once a month has been computed."""
        load_esg_feed(seeded_db, SAMPLE_FEED)
        compute_waci(seeded_db, AS_OF)
        body = client.get(ESG_URL).json()
        assert body["has_metric"] is True
        assert body["source"] == "computed"

    def test_portfolio_without_positions_reports_zero_coverage_not_an_error(self, client, seeded_db):
        """RP-48: a second, empty portfolio gets a metric row with no value and 0% coverage after compute."""
        add_portfolio(seeded_db, port_id="PF-EMPTY", account_no="2222222222")
        seeded_db.commit()
        load_esg_feed(seeded_db, SAMPLE_FEED)
        compute_waci(seeded_db, AS_OF)
        body = client.get("/api/portfolio/2222222222/esg").json()
        assert body["has_metric"] is True
        assert body["computed_value"] is None
        assert body["coverage_pct"] == 0
