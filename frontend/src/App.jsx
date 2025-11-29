import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import { DateRangeProvider } from './context/DateRangeContext';
import KPICards from './components/KPICards';
import RevenueChart from './components/RevenueChart';
import ScenarioBuilder from './components/ScenarioBuilder';
import CampaignPerformance from './components/CampaignPerformance';
import DateRangeSelector from './components/DateRangeSelector';
import EngagementKPIs from './components/EngagementKPIs';
import './components/DashboardLayout.css';
import './App.css';

const queryClient = new QueryClient();

function ThemeToggle() {
  const { isDarkMode, toggleTheme } = useTheme();
  return (
    <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle Dark Mode">
      {isDarkMode ? '🌞' : '🌙'}
    </button>
  );
}

function AppContent() {
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <div className="logo-section">
              <img src="/logo.png" alt="SurfNetworks" className="logo" />
              <div className="title-section">
                <h1>Arbitrage Dashboard</h1>
                <p className="subtitle">Real-time Profitability Tracking</p>
              </div>
            </div>
          </div>
          <div className="header-right">
            <div className="sync-status">
              <span className="status-dot"></span>
              Live Sync (15m)
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="dashboard-header-grid">
          <div className="left-kpi-column">
            <KPICards />
            <EngagementKPIs />
          </div>
          <div className="right-sidebar">
            <DateRangeSelector />
          </div>
        </div>
        <CampaignPerformance />
        <RevenueChart />
        <ScenarioBuilder />
      </main>

      <footer className="app-footer">
        <p>© 2023 AI Campaign Manager. All systems operational.</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <DateRangeProvider>
          <AppContent />
        </DateRangeProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
