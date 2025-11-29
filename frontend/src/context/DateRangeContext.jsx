import { createContext, useContext, useState, useCallback } from 'react';
import {
    startOfToday,
    endOfToday,
    startOfYesterday,
    endOfYesterday,
    subDays,
    startOfWeek,
    endOfWeek,
    subWeeks,
    startOfMonth,
    endOfMonth,
    subMonths,
    differenceInDays,
    format,
    parseISO
} from 'date-fns';

const DateRangeContext = createContext();

export const useDateRange = () => {
    const context = useContext(DateRangeContext);
    if (!context) {
        throw new Error('useDateRange must be used within DateRangeProvider');
    }
    return context;
};

// Preset calculations with exact date ranges
const calculatePreset = (presetKey) => {
    const today = startOfToday();

    const presets = {
        today: {
            start: startOfToday(),
            end: endOfToday()
        },
        yesterday: {
            start: startOfYesterday(),
            end: endOfYesterday()
        },
        last_7_days: {
            start: subDays(today, 7),
            end: endOfYesterday()
        },
        last_14_days: {
            start: subDays(today, 14),
            end: endOfYesterday()
        },
        last_28_days: {
            start: subDays(today, 28),
            end: endOfYesterday()
        },
        this_week: {
            start: startOfWeek(today, { weekStartsOn: 1 }), // Monday
            end: endOfWeek(today, { weekStartsOn: 1 })
        },
        last_week: {
            start: startOfWeek(subWeeks(today, 1), { weekStartsOn: 1 }),
            end: endOfWeek(subWeeks(today, 1), { weekStartsOn: 1 })
        },
        this_month: {
            start: startOfMonth(today),
            end: endOfMonth(today)
        },
        last_month: {
            start: startOfMonth(subMonths(today, 1)),
            end: endOfMonth(subMonths(today, 1))
        }
    };

    return presets[presetKey] || presets.last_7_days;
};

// Calculate comparison period (previous period of same length)
const calculateComparisonPeriod = (primaryRange) => {
    const daysDiff = differenceInDays(primaryRange.end, primaryRange.start);
    const comparisonEnd = subDays(primaryRange.start, 1);
    const comparisonStart = subDays(comparisonEnd, daysDiff);

    return {
        start: comparisonStart,
        end: comparisonEnd
    };
};

// Format date for API (YYYY-MM-DD)
export const formatDateForAPI = (date) => {
    return format(date, 'yyyy-MM-dd');
};

// Format date for display
export const formatDateForDisplay = (date) => {
    return format(date, 'MMM d, yyyy');
};

export const DateRangeProvider = ({ children }) => {
    // Initialize with last 7 days
    const initialRange = calculatePreset('last_7_days');

    const [primaryRange, setPrimaryRange] = useState({
        start: initialRange.start,
        end: initialRange.end,
        preset: 'last_7_days'
    });

    const [comparisonRange, setComparisonRange] = useState(null);
    const [isComparing, setIsComparing] = useState(false);

    // Set preset range
    const setPreset = useCallback((presetKey) => {
        const range = calculatePreset(presetKey);
        setPrimaryRange({
            start: range.start,
            end: range.end,
            preset: presetKey
        });

        // Auto-calculate comparison if enabled
        if (isComparing) {
            const comparison = calculateComparisonPeriod(range);
            setComparisonRange({
                start: comparison.start,
                end: comparison.end,
                preset: null
            });
        }
    }, [isComparing]);

    // Set custom range
    const setCustomRange = useCallback((start, end) => {
        // Validation
        if (start > end) {
            console.error('Start date cannot be after end date');
            return;
        }

        if (end > endOfToday()) {
            console.error('End date cannot be in the future');
            return;
        }

        const daysDiff = differenceInDays(end, start);
        if (daysDiff > 365) {
            console.error('Date range cannot exceed 365 days');
            return;
        }

        setPrimaryRange({
            start,
            end,
            preset: null // Custom range
        });

        // Auto-calculate comparison if enabled
        if (isComparing) {
            const comparison = calculateComparisonPeriod({ start, end });
            setComparisonRange({
                start: comparison.start,
                end: comparison.end,
                preset: null
            });
        }
    }, [isComparing]);

    // Toggle comparison mode
    const toggleComparison = useCallback(() => {
        const newIsComparing = !isComparing;
        setIsComparing(newIsComparing);

        if (newIsComparing) {
            // Enable comparison - calculate previous period
            const comparison = calculateComparisonPeriod(primaryRange);
            setComparisonRange({
                start: comparison.start,
                end: comparison.end,
                preset: null
            });
        } else {
            // Disable comparison
            setComparisonRange(null);
        }
    }, [isComparing, primaryRange]);

    // Set custom comparison range
    const setCustomComparisonRange = useCallback((start, end) => {
        if (!isComparing) return;

        setComparisonRange({
            start,
            end,
            preset: null
        });
    }, [isComparing]);

    const value = {
        primaryRange,
        comparisonRange,
        isComparing,
        setPreset,
        setCustomRange,
        toggleComparison,
        setCustomComparisonRange,
        formatDateForAPI,
        formatDateForDisplay
    };

    return (
        <DateRangeContext.Provider value={value}>
            {children}
        </DateRangeContext.Provider>
    );
};
