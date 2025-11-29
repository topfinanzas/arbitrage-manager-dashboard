import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDateRange } from '../context/DateRangeContext';
import { api } from '../api/client';
import './CampaignPerformance.css';

const CampaignPerformance = () => {
    const [activeTab, setActiveTab] = useState('adset'); // 'campaign', 'adset', 'ad'
    const { primaryRange } = useDateRange();

    // Fetch campaigns data
    const { data, isLoading, error } = useQuery({
        queryKey: ['campaigns', activeTab, primaryRange.start, primaryRange.end],
        queryFn: () => api.getCampaigns(
            activeTab,
            primaryRange.start,
            primaryRange.end
        ),
        enabled: !!primaryRange.start && !!primaryRange.end,
    });

    const campaigns = data?.data || [];

    // Export to Google Sheets (OAuth flow)
    const handleExportToSheets = async () => {
        try {
            // Check if already authenticated
            let sessionId = localStorage.getItem('google_session_id');

            if (!sessionId) {
                // Get authorization URL from backend
                const authResponse = await fetch('http://localhost:8080/api/auth/google');
                const { auth_url } = await authResponse.json();

                // Open OAuth popup
                const popup = window.open(
                    auth_url,
                    'Google OAuth',
                    'width=600,height=700'
                );

                // Wait for OAuth callback
                const newSessionId = await new Promise((resolve, reject) => {
                    const checkInterval = setInterval(() => {
                        try {
                            // Check if popup was closed
                            if (popup.closed) {
                                clearInterval(checkInterval);
                                reject(new Error('Authentication cancelled'));
                                return;
                            }

                            // Check for session ID in popup URL params (after redirect)
                            // We wrap this in try-catch because accessing location on cross-origin (during auth) throws error
                            try {
                                if (popup.location.hostname === window.location.hostname) {
                                    const urlParams = new URLSearchParams(popup.location.search);
                                    const authSuccess = urlParams.get('auth_success');
                                    const newSessionId = urlParams.get('session_id');

                                    if (authSuccess === 'true' && newSessionId) {
                                        clearInterval(checkInterval);
                                        popup.close();

                                        // Store session ID
                                        localStorage.setItem('google_session_id', newSessionId);
                                        resolve(newSessionId);
                                    }
                                }
                            } catch (e) {
                                // Ignore cross-origin errors while on google.com
                            }
                        } catch (e) {
                            // Ignore other errors
                        }
                    }, 500);

                    // Timeout after 5 minutes
                    setTimeout(() => {
                        clearInterval(checkInterval);
                        if (!popup.closed) popup.close();
                        reject(new Error('Authentication timeout'));
                    }, 300000);
                });

                sessionId = newSessionId;
            }

            // Export to sheets
            const startDate = primaryRange.start.toISOString().split('T')[0];
            const endDate = primaryRange.end.toISOString().split('T')[0];

            const exportResponse = await fetch('http://localhost:8080/api/export-to-sheets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    date_from: startDate,
                    date_to: endDate,
                }),
            });

            if (!exportResponse.ok) {
                const error = await exportResponse.json();
                throw new Error(error.detail || 'Export failed');
            }

            const { spreadsheet_url } = await exportResponse.json();

            // Open spreadsheet in new tab
            window.open(spreadsheet_url, '_blank');

        } catch (error) {
            console.error('Error exporting to sheets:', error);

            // Clear session if authentication error
            if (error.message.includes('authenticated')) {
                localStorage.removeItem('google_session_id');
            }

            alert(`Error: ${error.message}`);
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
        }).format(value);
    };

    const formatNumber = (value) => {
        return new Intl.NumberFormat('en-US').format(value);
    };

    const formatPercent = (value) => {
        return `${(value * 100).toFixed(2)}%`;
    };

    const getProfitClass = (profit) => {
        if (profit > 0) return 'positive';
        if (profit < 0) return 'negative';
        return '';
    };

    const getROASClass = (roas) => {
        if (roas >= 0.5) return 'excellent'; // 50% or better
        if (roas >= 0) return 'profitable'; // Positive
        if (roas >= -0.3) return 'break-even'; // -30% or better
        return 'loss'; // Worse than -30%
    };

    return (
        <div className="campaign-performance-container">
            <div className="module-header">
                <span className="module-icon">📈</span>
                <h2 className="module-title">Campaign Performance</h2>
            </div>

            {/* Tabs and Export Button */}
            <div className="performance-tabs">
                <div className="tabs-group">
                    <button
                        className={`tab-btn ${activeTab === 'campaign' ? 'active' : ''}`}
                        onClick={() => setActiveTab('campaign')}
                    >
                        Campaigns
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'adset' ? 'active' : ''}`}
                        onClick={() => setActiveTab('adset')}
                    >
                        Ad Groups
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'ad' ? 'active' : ''}`}
                        onClick={() => setActiveTab('ad')}
                    >
                        Ads
                    </button>
                </div>
                <button
                    className="export-btn"
                    onClick={handleExportToSheets}
                    title="Export to Google Sheets"
                >
                    📥 Export
                </button>
            </div>

            {/* Table */}
            <div className="performance-table-container">
                {isLoading && <div className="loading">Loading...</div>}
                {error && <div className="error">Error loading data</div>}

                {!isLoading && !error && campaigns.length === 0 && (
                    <div className="empty-state">No data available for this period</div>
                )}

                {!isLoading && !error && campaigns.length > 0 && (
                    <table className="performance-table">
                        <thead>
                            <tr>
                                <th>{activeTab === 'campaign' ? 'Campaign ID' : (activeTab === 'adset' ? 'Ad Group ID' : 'Ad ID')}</th>
                                <th>{activeTab === 'campaign' ? 'Campaign' : (activeTab === 'adset' ? 'Ad Group' : 'Ad')}</th>
                                <th>Spend</th>
                                <th>Revenue</th>
                                <th>Profit</th>
                                <th>ROAS</th>
                                <th>Visitors (Meta)</th>
                                <th>Eventos de Búsqueda</th>
                                <th>Costo de Búsqueda</th>
                                <th>Eventos de Compra</th>
                                <th>Costo de Compra</th>
                                <th>Widget CTR</th>
                                <th>Clicks Pagos</th>
                                <th>RPC Prom</th>
                            </tr>
                        </thead>
                        <tbody>
                            {campaigns.map((row, index) => (
                                <tr key={`${row.id}-${index}`}>
                                    <td>{row.id}</td>
                                    <td>{row.name}</td>
                                    <td>{formatCurrency(row.spend)}</td>
                                    <td>{formatCurrency(row.revenue)}</td>
                                    <td className={getProfitClass(row.profit)}>
                                        {formatCurrency(row.profit)}
                                    </td>
                                    <td className={getROASClass(row.roas)}>
                                        {(row.roas * 100).toFixed(0)}%
                                    </td>
                                    <td>{formatNumber(row.visitors)}</td>
                                    <td>{formatNumber(row.eventos_busqueda)}</td>
                                    <td>{formatCurrency(row.costo_busqueda)}</td>
                                    <td>{formatNumber(row.eventos_compra)}</td>
                                    <td>{formatCurrency(row.costo_compra)}</td>
                                    <td>{formatPercent(row.widget_ctr / 100)}</td>
                                    <td>{formatNumber(row.clicks_pagos)}</td>
                                    <td>{formatCurrency(row.rpc_prom)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default CampaignPerformance;
