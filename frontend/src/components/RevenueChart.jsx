import { useQuery } from '@tanstack/react-query';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import { api } from '../api/client';
import './RevenueChart.css';

export default function RevenueChart() {
    // For now, we'll use mock data since the API endpoint for daily history isn't ready yet
    // In a real scenario, we would fetch this from api.getDailyHistory()
    const mockData = [
        { date: '2023-11-20', revenue: 120, spend: 150, profit: -30 },
        { date: '2023-11-21', revenue: 180, spend: 160, profit: 20 },
        { date: '2023-11-22', revenue: 250, spend: 180, profit: 70 },
        { date: '2023-11-23', revenue: 310, spend: 200, profit: 110 },
        { date: '2023-11-24', revenue: 280, spend: 210, profit: 70 },
        { date: '2023-11-25', revenue: 350, spend: 220, profit: 130 },
        { date: '2023-11-26', revenue: 420, spend: 230, profit: 190 },
    ];

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
        }).format(value);
    };

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="tooltip-date">{label}</p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ color: entry.color }}>
                            {entry.name}: {formatCurrency(entry.value)}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="chart-section">
            <div className="chart-header">
                <h2>📈 Revenue vs Spend Trend</h2>
            </div>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height={350}>
                    <AreaChart
                        data={mockData}
                        margin={{
                            top: 10,
                            right: 30,
                            left: 0,
                            bottom: 0,
                        }}
                    >
                        <defs>
                            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                        <XAxis
                            dataKey="date"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#9ca3af', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#9ca3af', fontSize: 12 }}
                            tickFormatter={(value) => `$${value}`}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend iconType="circle" />
                        <Area
                            type="monotone"
                            dataKey="revenue"
                            name="Revenue"
                            stroke="#10b981"
                            fillOpacity={1}
                            fill="url(#colorRevenue)"
                            strokeWidth={3}
                        />
                        <Area
                            type="monotone"
                            dataKey="spend"
                            name="Spend"
                            stroke="#ef4444"
                            fillOpacity={1}
                            fill="url(#colorSpend)"
                            strokeWidth={3}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
