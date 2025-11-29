import { useState, useEffect } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Cell
} from 'recharts';
import './ScenarioBuilder.css';
import axios from 'axios';

export default function ScenarioBuilder() {
    // Initial state based on typical arbitrage metrics
    const [inputs, setInputs] = useState({
        spend: 500,
        cpc: 0.15,
        linkCtr: 2.5, // %
        widgetCtr: 25, // %
        rpc: 0.08, // Revenue per Widget Click
    });
    const [loading, setLoading] = useState(true);

    const [results, setResults] = useState({
        visitors: 0,
        widgetClicks: 0,
        revenue: 0,
        profit: 0,
        roas: 0,
    });



    // Fetch current metrics on mount
    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/analytics/current-metrics`);
                const data = response.data;
                setInputs(prev => ({
                    ...prev,
                    spend: data.spend,
                    cpc: data.cpc,
                    widgetCtr: data.widget_ctr,
                    rpc: data.rpc
                }));
            } catch (error) {
                console.error("Failed to fetch current metrics:", error);
                // Keep defaults on error
            } finally {
                setLoading(false);
            }
        };

        fetchMetrics();
    }, []);

    // Calculate results whenever inputs change
    useEffect(() => {
        const spend = inputs.spend || 0;
        const cpc = inputs.cpc || 0.01; // Avoid division by zero
        const widgetCtr = inputs.widgetCtr || 0;
        const rpc = inputs.rpc || 0;

        const visitors = cpc > 0 ? Math.round(spend / cpc) : 0;
        const widgetClicks = Math.round(visitors * (widgetCtr / 100));
        const revenue = widgetClicks * rpc;
        const profit = revenue - spend;
        const roas = spend > 0 ? revenue / spend : 0;

        setResults({
            visitors,
            widgetClicks,
            revenue: isNaN(revenue) ? 0 : revenue,
            profit: isNaN(profit) ? 0 : profit,
            roas: isNaN(roas) ? 0 : roas,
        });
    }, [inputs]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setInputs((prev) => ({
            ...prev,
            [name]: parseFloat(value),
        }));
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
        }).format(value);
    };

    const chartData = [
        { name: 'Spend', value: inputs.spend },
        { name: 'Revenue', value: results.revenue },
        { name: 'Profit', value: results.profit },
    ];

    return (
        <div className="scenario-builder">
            <div className="scenario-header">
                <h2>🧪 Profitability Simulator</h2>
                <p>Adjust the levers to simulate different arbitrage scenarios.</p>
                {loading && <span className="loading-badge">Loading current metrics...</span>}
            </div>

            <div className="scenario-content">
                <div className="controls-section">
                    <div className="control-group">
                        <label>
                            Daily Spend
                            <span className="value-badge">{formatCurrency(inputs.spend)}</span>
                        </label>
                        <input
                            type="range"
                            name="spend"
                            min="50"
                            max="5000"
                            step="50"
                            value={inputs.spend}
                            onChange={handleInputChange}
                        />
                    </div>

                    <div className="control-group">
                        <label>
                            Meta CPC (Cost Per Click)
                            <span className="value-badge">{formatCurrency(inputs.cpc)}</span>
                        </label>
                        <input
                            type="range"
                            name="cpc"
                            min="0.01"
                            max="1.00"
                            step="0.01"
                            value={inputs.cpc}
                            onChange={handleInputChange}
                        />
                    </div>

                    <div className="control-group">
                        <label>
                            Widget CTR (Landing Page)
                            <span className="value-badge">{inputs.widgetCtr}%</span>
                        </label>
                        <input
                            type="range"
                            name="widgetCtr"
                            min="5"
                            max="100"
                            step="1"
                            value={inputs.widgetCtr}
                            onChange={handleInputChange}
                        />
                    </div>

                    <div className="control-group">
                        <label>
                            RPC (Revenue Per Click)
                            <span className="value-badge">{formatCurrency(inputs.rpc)}</span>
                        </label>
                        <input
                            type="range"
                            name="rpc"
                            min="0.01"
                            max="0.50"
                            step="0.01"
                            value={inputs.rpc}
                            onChange={handleInputChange}
                        />
                    </div>
                </div>

                <div className="results-section">
                    <div className="metrics-grid">
                        <div className="metric-card">
                            <span className="metric-label">Projected ROAS</span>
                            <span className={`metric-value ${results.roas >= 1 ? 'positive' : 'negative'}`}>
                                {results.roas.toFixed(2)}x
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Projected Profit</span>
                            <span className={`metric-value ${results.profit >= 0 ? 'positive' : 'negative'}`}>
                                {formatCurrency(results.profit)}
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Break-even CPC</span>
                            <span className="metric-value neutral">
                                {formatCurrency((inputs.widgetCtr / 100) * inputs.rpc)}
                            </span>
                            <span className="metric-sublabel">Max affordable cost</span>
                        </div>
                    </div>

                    <div className="chart-wrapper">
                        <ResponsiveContainer width="100%" height={200}>
                            <BarChart data={chartData} layout="vertical" margin={{ left: 40 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" width={60} />
                                <Tooltip formatter={(value) => formatCurrency(value)} />
                                <ReferenceLine x={0} stroke="#666" />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                    {chartData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={
                                                entry.name === 'Spend' ? '#ef4444' :
                                                    entry.name === 'Revenue' ? '#10b981' :
                                                        entry.value >= 0 ? '#3b82f6' : '#f59e0b'
                                            }
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
