import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import './CampaignsTable.css';

export default function CampaignsTable() {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const { data: campaigns, isLoading, error } = useQuery({
    queryKey: ['campaigns'],
    queryFn: api.getCampaigns,
    refetchInterval: 60000,
  });

  if (isLoading) {
    return <div className="table-loading">Loading campaigns...</div>;
  }

  if (error) {
    return <div className="error">Error loading campaigns: {error.message}</div>;
  }

  const filteredCampaigns = campaigns.filter((campaign) => {
    const matchesSearch = campaign.ad_set_name
      .toLowerCase()
      .includes(searchTerm.toLowerCase());

    if (filter === 'all') return matchesSearch;
    if (filter === 'profitable') return matchesSearch && campaign.roas >= 1.0;
    if (filter === 'loss') return matchesSearch && campaign.roas < 1.0;
    if (filter === 'critical') return matchesSearch && campaign.roas < 0.5;

    return matchesSearch;
  });

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const getROASClass = (roas) => {
    if (roas >= 1.5) return 'excellent';
    if (roas >= 1.0) return 'profitable';
    if (roas >= 0.7) return 'break-even';
    return 'loss';
  };

  return (
    <div className="campaigns-section">
      <div className="campaigns-header">
        <h2>📊 Campaign Performance</h2>
        <div className="campaigns-controls">
          <input
            type="text"
            placeholder="🔍 Search campaigns..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <div className="filter-buttons">
            <button
              className={filter === 'all' ? 'active' : ''}
              onClick={() => setFilter('all')}
            >
              All ({campaigns.length})
            </button>
            <button
              className={filter === 'profitable' ? 'active' : ''}
              onClick={() => setFilter('profitable')}
            >
              ✅ Profitable
            </button>
            <button
              className={filter === 'loss' ? 'active' : ''}
              onClick={() => setFilter('loss')}
            >
              ⚠️ Loss
            </button>
            <button
              className={filter === 'critical' ? 'active critical' : ''}
              onClick={() => setFilter('critical')}
            >
              🚨 Critical
            </button>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="campaigns-table">
          <thead>
            <tr>
              <th>Campaign</th>
              <th>Market</th>
              <th>Spend</th>
              <th>Revenue</th>
              <th>Profit</th>
              <th>ROAS</th>
              <th>Visitors</th>
              <th>Widget CTR</th>
              <th>RPC</th>
            </tr>
          </thead>
          <tbody>
            {filteredCampaigns.length === 0 ? (
              <tr>
                <td colSpan="9" className="no-results">
                  No campaigns found
                </td>
              </tr>
            ) : (
              filteredCampaigns.map((campaign) => (
                <tr key={campaign.ad_set_id}>
                  <td className="campaign-name">
                    <div className="name-cell">
                      <span className="name">{campaign.ad_set_name}</span>
                      <span className="id">ID: {campaign.ad_set_id}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`market-badge ${campaign.market.toLowerCase()}`}>
                      {campaign.market}
                    </span>
                  </td>
                  <td>{formatCurrency(campaign.spend)}</td>
                  <td>{formatCurrency(campaign.revenue)}</td>
                  <td className={campaign.profit >= 0 ? 'positive' : 'negative'}>
                    {formatCurrency(campaign.profit)}
                  </td>
                  <td>
                    <span className={`roas-badge ${getROASClass(campaign.roas)}`}>
                      {campaign.roas.toFixed(2)}x
                    </span>
                  </td>
                  <td>{campaign.link_clicks.toLocaleString()}</td>
                  <td>{(campaign.widget_ctr * 100).toFixed(1)}%</td>
                  <td>{formatCurrency(campaign.rpc)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
