import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useDateRange } from '../context/DateRangeContext';
import './EngagementKPIs.css';

export default function EngagementKPIs() {
    const { primaryRange, comparisonRange, isComparing, formatDateForAPI } = useDateRange();

    const { data: kpis, isLoading, error } = useQuery({
        queryKey: ['kpis', primaryRange, comparisonRange],
        queryFn: () => api.getKPIs(
            formatDateForAPI(primaryRange.start),
            formatDateForAPI(primaryRange.end),
            comparisonRange ? formatDateForAPI(comparisonRange.start) : null,
            comparisonRange ? formatDateForAPI(comparisonRange.end) : null
        ),
        refetchInterval: 60000,
    });

    if (isLoading) return <div className="loading">Loading Engagement KPIs...</div>;
    if (error) return null; // Fail silently or show error

    const primary = kpis.primary || kpis;
    const comparison = kpis.comparison || null;

    const calculateDelta = (current, previous) => {
        if (!previous || previous === 0) return null;
        return ((current - previous) / previous) * 100;
    };

    const formatDelta = (delta, isInverse = false) => {
        if (delta === null || delta === undefined) return null;

        const absValue = Math.abs(delta).toFixed(1);
        const isPositive = delta > 0;

        // Standard: Increase is good (Green), Decrease is bad (Red)
        // Inverse (Cost): Increase is bad (Red), Decrease is good (Green)
        const isGood = isInverse ? !isPositive : isPositive;

        const arrow = isPositive ? '↑' : '↓';
        const className = isGood ? 'kpi-delta delta-positive' : 'kpi-delta delta-negative';

        return <div className={className}>{arrow} {absValue}%</div>;
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

    return (
        <div className="engagement-kpis-container">
            <h2 className="section-title">
                <span className="module-icon">🖱️</span>
                Engagement KPIs
            </h2>

            <div className="engagement-main-grid">
                {/* Meta Section */}
                <div className="platform-column">
                    <div className="platform-logo-container">
                        <img src="/meta-logo.jpg" alt="Meta" className="platform-logo meta-logo" />
                    </div>
                    <div className="cards-grid">
                        <div className="kpi-card compact">
                            <div className="kpi-icon">🔍</div>
                            <div className="kpi-content">
                                <div className="kpi-label">Evento Búsqueda</div>
                                <div className="kpi-value">{formatNumber(primary.total_searches)}</div>
                                {isComparing && comparison && formatDelta(calculateDelta(primary.total_searches, comparison.total_searches))}
                            </div>
                        </div>
                        <div className="kpi-card compact">
                            <div className="kpi-icon">💰</div>
                            <div className="kpi-content">
                                <div className="kpi-label">Costo por Búsqueda</div>
                                <div className="kpi-value">{formatCurrency(primary.cost_per_search)}</div>
                                {isComparing && comparison && formatDelta(calculateDelta(primary.cost_per_search, comparison.cost_per_search), true)}
                            </div>
                        </div>
                        <div className="kpi-card compact">
                            <div className="kpi-icon">🏷️</div>
                            <div className="kpi-content">
                                <div className="kpi-label">Evento Compra</div>
                                <div className="kpi-value">{formatNumber(primary.total_purchases)}</div>
                                {isComparing && comparison && formatDelta(calculateDelta(primary.total_purchases, comparison.total_purchases))}
                            </div>
                        </div>
                        <div className="kpi-card compact">
                            <div className="kpi-icon">💳</div>
                            <div className="kpi-content">
                                <div className="kpi-label">Costo por Compra</div>
                                <div className="kpi-value">{formatCurrency(primary.cost_per_purchase)}</div>
                                {isComparing && comparison && formatDelta(calculateDelta(primary.cost_per_purchase, comparison.cost_per_purchase), true)}
                            </div>
                        </div>
                    </div>
                </div>

                {/* System1 Section */}
                <div className="platform-column">
                    <div className="platform-logo-container">
                        <img src="/system1-logo.png" alt="System1" className="platform-logo system1-logo" />
                    </div>
                    <div className="cards-grid">
                        <div className="kpi-card compact">
                            <div className="kpi-icon">🖱️</div>
                            <div className="kpi-content">
                                <div className="kpi-label">CTR% Widget</div>
                                <div className="kpi-value">{formatPercent(primary.avg_widget_ctr)}</div>
                                {isComparing && comparison && formatDelta(calculateDelta(primary.avg_widget_ctr, comparison.avg_widget_ctr))}
                            </div>
                        </div>
                        <div className="kpi-card compact">
                            <div className="kpi-icon">👆</div>
                            <div className="kpi-content">
                                <div className="kpi-label">Clicks Pagos</div>
                                <div className="kpi-value">{formatNumber(primary.total_widget_clicks)}</div>
                                {isComparing && comparison && formatDelta(calculateDelta(primary.total_widget_clicks, comparison.total_widget_clicks))}
                            </div>
                        </div>
                        <div className="kpi-card compact">
                            <div className="kpi-icon">💵</div>
                            <div className="kpi-content">
                                <div className="kpi-label">RPC Prom.</div>
                                <div className="kpi-value">{formatCurrency(primary.avg_rpc)}</div>
                                {isComparing && comparison && formatDelta(calculateDelta(primary.avg_rpc, comparison.avg_rpc))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
