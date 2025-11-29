import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useDateRange } from '../context/DateRangeContext';
import './KPICards.css';

export default function KPICards() {
    const { primaryRange, comparisonRange, isComparing, formatDateForAPI } = useDateRange();

    const { data: kpis, isLoading, error } = useQuery({
        queryKey: ['kpis', primaryRange, comparisonRange],
        queryFn: () => api.getKPIs(
            formatDateForAPI(primaryRange.start),
            formatDateForAPI(primaryRange.end),
            comparisonRange ? formatDateForAPI(comparisonRange.start) : null,
            comparisonRange ? formatDateForAPI(comparisonRange.end) : null
        ),
        refetchInterval: 60000, // Refetch every minute
    });

    if (isLoading) {
        return (
            <div className="kpi-cards loading">
                <div className="kpi-card skeleton"></div>
                <div className="kpi-card skeleton"></div>
                <div className="kpi-card skeleton"></div>
                <div className="kpi-card skeleton"></div>
            </div>
        );
    }

    if (error) {
        return <div className="error">Error loading KPIs: {error.message}</div>;
    }

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
        }).format(value);
    };

    const getROASClass = (roas) => {
        // ROAS is now percentage: 0.5 = 50%, 0 = breakeven, -0.3 = -30%
        if (roas >= 0.5) return 'excellent';      // +50% or more
        if (roas >= 0.0) return 'profitable';     // 0% to +50%
        if (roas >= -0.3) return 'break-even';    // -30% to 0%
        return 'loss';                            // worse than -30%
    };

    // Calculate delta percentage
    const calculateDelta = (current, previous) => {
        if (!previous || previous === 0) return null;
        return ((current - previous) / previous) * 100;
    };

    // Format delta for display
    const formatDelta = (delta, isInverse = false) => {
        if (delta === null || delta === undefined) return null;

        const absValue = Math.abs(delta).toFixed(1);
        const isPositive = delta > 0;

        // For spend, increase is bad (red), decrease is good (green)
        // For revenue/profit/roas, increase is good (green), decrease is bad (red)
        const isGood = isInverse ? !isPositive : isPositive;
        const arrow = isPositive ? '↑' : '↓';
        const className = isGood ? 'delta-positive' : 'delta-negative';

        return { text: `${arrow} ${absValue}%`, className };
    };

    // Extract primary and comparison data
    const primary = kpis.primary || kpis;
    const comparison = kpis.comparison || null;

    return (
        <div className="kpi-module">
            <div className="module-header">
                <span className="module-icon">📊</span>
                <h2 className="module-title">Main KPIs</h2>
            </div>
            <div className="kpi-cards">
                {/* Total Spend */}
                <div className="kpi-card compact">
                    <div className="kpi-icon">💲</div>
                    <div className="kpi-content">
                        <div className="kpi-label">Total Spend</div>
                        <div className="kpi-value">{formatCurrency(primary.total_spend)}</div>
                        {isComparing && comparison && (
                            <div className={formatDelta(calculateDelta(primary.total_spend, comparison.total_spend), true)?.className}>
                                {formatDelta(calculateDelta(primary.total_spend, comparison.total_spend), true)?.text}
                            </div>
                        )}
                    </div>
                </div>

                {/* Total Revenue */}
                <div className="kpi-card compact">
                    <div className="kpi-icon">⬆️</div>
                    <div className="kpi-content">
                        <div className="kpi-label">Total Revenue</div>
                        <div className="kpi-value">{formatCurrency(primary.total_revenue)}</div>
                        {isComparing && comparison && (
                            <div className={formatDelta(calculateDelta(primary.total_revenue, comparison.total_revenue))?.className}>
                                {formatDelta(calculateDelta(primary.total_revenue, comparison.total_revenue))?.text}
                            </div>
                        )}
                    </div>
                </div>

                {/* Total Profit */}
                <div className="kpi-card compact">
                    <div className="kpi-icon">➖</div>
                    <div className="kpi-content">
                        <div className="kpi-label">Total Profit</div>
                        <div className={`kpi-value ${primary.total_profit >= 0 ? 'positive' : 'negative'}`}>
                            {formatCurrency(primary.total_profit)}
                        </div>
                        {isComparing && comparison && (
                            <div className={formatDelta(calculateDelta(primary.total_profit, comparison.total_profit))?.className}>
                                {formatDelta(calculateDelta(primary.total_profit, comparison.total_profit))?.text}
                            </div>
                        )}
                    </div>
                </div>

                {/* Average ROAS */}
                <div className="kpi-card compact">
                    <div className="kpi-icon">％</div>
                    <div className="kpi-content">
                        <div className="kpi-label">Average ROAS</div>
                        <div className={`kpi-value ${getROASClass(primary.avg_roas)}`}>
                            {(primary.avg_roas * 100).toFixed(0)}%
                        </div>
                        {isComparing && comparison && (
                            <div className={formatDelta(calculateDelta(primary.avg_roas, comparison.avg_roas))?.className}>
                                {formatDelta(calculateDelta(primary.avg_roas, comparison.avg_roas))?.text}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
