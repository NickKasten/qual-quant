-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    strategy VARCHAR(50) NOT NULL,
    profit_loss DECIMAL(20, 8),
    status VARCHAR(10) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create positions table with ON CONFLICT handling
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    quantity DECIMAL(20, 8) NOT NULL,
    average_entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8) NOT NULL,
    unrealized_pnl DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create equity table with timestamp-based uniqueness
CREATE TABLE IF NOT EXISTS equity (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL UNIQUE,
    equity DECIMAL(20, 8) NOT NULL,
    cash DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create signals table with composite unique constraint
CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(4) NOT NULL CHECK (signal_type IN ('buy', 'sell', 'hold')),
    strength DECIMAL(5, 4) NOT NULL CHECK (strength >= 0 AND strength <= 1),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    strategy VARCHAR(50) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol, timestamp, strategy)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity(timestamp);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for positions table
CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 
