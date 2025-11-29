import { format } from 'date-fns';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://arbitrage-api-834716206048.us-central1.run.app';

const formatDate = (date) => {
    if (!date) return null;
    if (date instanceof Date) {
        return format(date, 'yyyy-MM-dd');
    }
    return date; // Assume it's already a string
};

export const api = {
    getKPIs: async (startDate, endDate, comparisonStart = null, comparisonEnd = null) => {
        const params = new URLSearchParams({
            start_date: formatDate(startDate),
            end_date: formatDate(endDate)
        });

        if (comparisonStart && comparisonEnd) {
            params.append('comparison_start', formatDate(comparisonStart));
            params.append('comparison_end', formatDate(comparisonEnd));
        }

        const response = await fetch(`${API_BASE_URL}/api/kpis?${params}`);
        if (!response.ok) throw new Error('Failed to fetch KPIs');
        return response.json();
    },

    getCampaigns: async (level = 'adset', startDate, endDate) => {
        const params = new URLSearchParams({
            level: level,
            date_from: formatDate(startDate),
            date_to: formatDate(endDate)
        });

        const response = await fetch(`${API_BASE_URL}/api/campaigns?${params}`);
        if (!response.ok) throw new Error('Failed to fetch campaigns');
        return response.json();
    },

    getAlerts: async () => {
        const response = await fetch(`${API_BASE_URL}/api/alerts`);
        if (!response.ok) throw new Error('Failed to fetch alerts');
        return response.json();
    },

    syncData: async () => {
        const response = await fetch(`${API_BASE_URL}/api/sync`, {
            method: 'POST',
        });
        if (!response.ok) throw new Error('Failed to sync data');
        return response.json();
    },
};
