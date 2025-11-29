
import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import MagicMock, patch

client = TestClient(app)

def test_get_current_metrics_default():
    """Test that the endpoint returns defaults when BigQuery is not available"""
    # Mock BigQuery client to be None or raise error
    with patch('main.bq_client', None):
        response = client.get("/api/analytics/current-metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["cpc"] == 0.15
        assert data["rpc"] == 0.08
        assert data["widget_ctr"] == 25.0
        assert data["spend"] == 500.0

@patch('google.cloud.bigquery.Client')
def test_get_current_metrics_mocked(mock_bq_client):
    """Test that the endpoint returns calculated metrics from BigQuery results"""
    # Setup mock return values
    mock_query_job = MagicMock()
    mock_row = MagicMock()
    mock_row.total_spend = 1000.0
    mock_row.total_link_clicks = 5000
    mock_row.total_widget_clicks = 1000
    mock_row.total_revenue = 200.0
    
    mock_query_job.result.return_value = [mock_row]
    mock_bq_client.return_value.query.return_value = mock_query_job
    
    # We need to patch the global bq_client in main
    with patch('main.bq_client', mock_bq_client.return_value):
        response = client.get("/api/analytics/current-metrics")
        assert response.status_code == 200
        data = response.json()
        
        # Expected calculations:
        # CPC = 1000 / 5000 = 0.20
        # RPC = 200 / 1000 = 0.20
        # Widget CTR = (1000 / 5000) * 100 = 20.0
        # Avg Spend = 1000 / 7 = 143.0 (rounded)
        
        assert data["cpc"] == 0.20
        assert data["rpc"] == 0.20
        assert data["widget_ctr"] == 20.0
        assert data["spend"] == 143.0
