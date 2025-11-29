import { useDateRange } from '../context/DateRangeContext';
import './DateRangeSelector.css';

export default function DateRangeSelector() {
    const {
        primaryRange,
        comparisonRange,
        isComparing,
        setPreset,
        toggleComparison,
        formatDateForDisplay
    } = useDateRange();

    const presets = [
        { key: 'today', label: 'Hoy' },
        { key: 'yesterday', label: 'Ayer' },
        { key: 'last_7_days', label: 'Últimos 7 días' },
        { key: 'last_14_days', label: 'Últimos 14 días' },
        { key: 'last_28_days', label: 'Últimos 28 días' },
        { key: 'this_week', label: 'Esta semana' },
        { key: 'last_week', label: 'La semana pasada' },
        { key: 'this_month', label: 'Este mes' },
        { key: 'last_month', label: 'El mes pasado' }
    ];

    return (
        <div className="date-range-module">
            <div className="module-header">
                <span className="module-icon">📅</span>
                <h2 className="module-title">Date Range</h2>
            </div>
            <div className="date-range-content">
                <div className="preset-buttons">
                    {presets.map(preset => (
                        <button
                            key={preset.label}
                            className={`preset-btn ${primaryRange.preset === preset.key ? 'active' : ''}`}
                            onClick={() => setPreset(preset.key)}
                        >
                            {preset.label}
                        </button>
                    ))}
                </div>

                <div className="date-display">
                    <span className="date-label">Período:</span>
                    <span className="date-value">
                        {formatDateForDisplay(primaryRange.start)} - {formatDateForDisplay(primaryRange.end)}
                    </span>
                    {isComparing && comparisonRange && (
                        <>
                            <span className="vs-label">vs</span>
                            <span className="date-value comparison">
                                {formatDateForDisplay(comparisonRange.start)} - {formatDateForDisplay(comparisonRange.end)}
                            </span>
                        </>
                    )}
                </div>

                <div className="comparison-toggle">
                    <label className="checkbox-container">
                        <input
                            type="checkbox"
                            checked={isComparing}
                            onChange={toggleComparison}
                        />
                        <span className="checkmark"></span>
                        Comparar con período anterior
                    </label>
                </div>
            </div>
        </div>
    );
}
