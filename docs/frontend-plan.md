# Frontend Dashboard Architecture Plan

Based on the PRD and existing backend APIs, here's the complete plan for the dashboard frontend:

## Architecture Overview

**Frontend Stack**: Next.js + Tailwind CSS (as specified in PRD)
**Current State**: Empty frontend directory structure exists
**Backend APIs Available**: Portfolio, Trades, Performance, Signals, Status endpoints

## Component Architecture

### Core Components

1. **Layout Components**
   - `DisclaimerBanner` - Persistent legal banner (PRD requirement)
   - `Header` - Site navigation and branding
   - `Footer` - Additional disclaimers and links

2. **Dashboard Components**
   - `PortfolioSummary` - Current equity, P/L, positions overview
   - `PerformanceChart` - Equity curve vs benchmarks
   - `TradeFeed` - Real-time trade history with pagination
   - `SignalsPanel` - Current SMA/RSI indicators
   - `DataTimestamp` - Shows data delay (15 min requirement)

3. **Data Components**
   - `ApiClient` - Centralized API communication
   - `DataProvider` - React context for state management
   - `RefreshController` - Auto-refresh every 15 minutes

## Page Structure

```
pages/
├── index.js          # Main dashboard (Portfolio + Performance)
├── trades.js         # Detailed trade history
├── signals.js        # Strategy signals and methodology
├── about.js          # Strategy explanation (PRD requirement)
└── _app.js          # Global layout with disclaimer banner
```

## API Integration Strategy

**Base API URL**: Backend FastAPI endpoints
**Authentication**: API key in headers (existing auth system)
**Rate Limiting**: 30 requests/minute (per backend implementation)
**Data Refresh**: 15-minute intervals with manual refresh option

## Responsive Design Plan

**Framework**: Tailwind CSS
**Breakpoints**: Mobile-first (≥375px as per PRD)
**Color Scheme**: Neutral greys/blues (avoid casino colors per PRD)
**Accessibility**: WCAG 2.1 AA compliance with keyboard navigation

## Implementation Priority

**Day 5 Implementation Order:**
1. Next.js setup with package.json
2. Disclaimer banner (compliance requirement)
3. API client utility 
4. Portfolio summary (core dashboard feature)
5. Performance chart (key visual component)
6. Trade feed (transparency requirement)
7. Signals panel (strategy visibility)
8. Responsive styling and accessibility

## Task Breakdown

### High Priority Tasks
- [ ] Create Next.js project structure with package.json
- [ ] Implement DisclaimerBanner component
- [ ] Create API client utility for backend integration
- [ ] Build PortfolioSummary component

### Medium Priority Tasks
- [ ] Implement PerformanceChart component
- [ ] Create TradeFeed component with pagination
- [ ] Build SignalsPanel component
- [ ] Setup responsive Tailwind CSS configuration

### Low Priority Tasks
- [ ] Implement auto-refresh functionality
- [ ] Add accessibility features and keyboard navigation

This plan delivers all PRD requirements within the allocated Day 5 timeline, focusing on core dashboard functionality with proper disclaimers and data transparency.