-- Velox (NexlumeAI) — Initial Database Schema
-- PostgreSQL 16+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Hotels
-- ============================================================
CREATE TABLE hotels (
    id              SERIAL PRIMARY KEY,
    hotel_id        INTEGER UNIQUE NOT NULL,          -- PMS hotel ID (e.g. 21966)
    name_tr         VARCHAR(255) NOT NULL,
    name_en         VARCHAR(255) NOT NULL,
    hotel_type      VARCHAR(50) DEFAULT 'boutique',
    timezone        VARCHAR(50) DEFAULT 'Europe/Istanbul',
    currency_base   VARCHAR(3)  DEFAULT 'EUR',
    pms             VARCHAR(50) DEFAULT 'elektraweb',
    whatsapp_number VARCHAR(20),
    season_open     VARCHAR(5),                        -- MM-DD
    season_close    VARCHAR(5),                        -- MM-DD
    profile_json    JSONB NOT NULL DEFAULT '{}',       -- Full HOTEL_PROFILE
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Conversations
-- ============================================================
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    phone_hash      VARCHAR(64) NOT NULL,              -- SHA-256 of phone number
    phone_display   VARCHAR(20),                       -- Masked: +90 533 *** ** 77
    language        VARCHAR(5) DEFAULT 'tr',
    current_state   VARCHAR(30) DEFAULT 'GREETING',
    current_intent  VARCHAR(50),
    entities_json   JSONB DEFAULT '{}',
    risk_flags      TEXT[] DEFAULT '{}',
    is_active       BOOLEAN DEFAULT true,
    last_message_at TIMESTAMPTZ DEFAULT now(),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_conv_hotel_phone ON conversations(hotel_id, phone_hash);
CREATE INDEX idx_conv_active ON conversations(is_active, last_message_at DESC);

-- ============================================================
-- Messages
-- ============================================================
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    role            VARCHAR(10) NOT NULL,               -- 'user', 'assistant', 'system'
    content         TEXT NOT NULL,
    internal_json   JSONB,                              -- INTERNAL_JSON (assistant only)
    tool_calls      JSONB,                              -- Tool calls made
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_msg_conv ON messages(conversation_id, created_at);

-- ============================================================
-- Stay Holds
-- ============================================================
CREATE TABLE stay_holds (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hold_id         VARCHAR(30) UNIQUE NOT NULL,        -- S_HOLD_xxxx
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    conversation_id UUID REFERENCES conversations(id),
    draft_json      JSONB NOT NULL,                     -- Full booking draft
    status          VARCHAR(30) DEFAULT 'PENDING_APPROVAL',
    pms_reservation_id VARCHAR(50),                     -- Set after Elektraweb booking
    voucher_no      VARCHAR(50),
    approved_by     VARCHAR(50),
    approved_at     TIMESTAMPTZ,
    rejected_reason TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_stay_hotel_status ON stay_holds(hotel_id, status);

-- ============================================================
-- Restaurant Holds
-- ============================================================
CREATE TABLE restaurant_holds (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hold_id         VARCHAR(30) UNIQUE NOT NULL,        -- R_HOLD_xxxx
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    conversation_id UUID REFERENCES conversations(id),
    slot_id         VARCHAR(50),
    date            DATE NOT NULL,
    time            TIME NOT NULL,
    party_size      INTEGER NOT NULL,
    guest_name      VARCHAR(255),
    phone           VARCHAR(20),
    area            VARCHAR(20),                        -- indoor/outdoor
    notes           TEXT,
    status          VARCHAR(30) DEFAULT 'PENDING_APPROVAL',
    approved_by     VARCHAR(50),
    approved_at     TIMESTAMPTZ,
    rejected_reason TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_rest_hotel_date ON restaurant_holds(hotel_id, date);

-- ============================================================
-- Transfer Holds
-- ============================================================
CREATE TABLE transfer_holds (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hold_id         VARCHAR(30) UNIQUE NOT NULL,        -- TR_HOLD_xxxx
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    conversation_id UUID REFERENCES conversations(id),
    route           VARCHAR(100) NOT NULL,
    date            DATE NOT NULL,
    time            TIME NOT NULL,
    pax_count       INTEGER NOT NULL,
    guest_name      VARCHAR(255),
    phone           VARCHAR(20),
    flight_no       VARCHAR(20),
    vehicle_type    VARCHAR(30),
    baby_seat       BOOLEAN DEFAULT false,
    price_eur       DECIMAL(10,2),
    notes           TEXT,
    status          VARCHAR(30) DEFAULT 'PENDING_APPROVAL',
    approved_by     VARCHAR(50),
    approved_at     TIMESTAMPTZ,
    rejected_reason TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_transfer_hotel_date ON transfer_holds(hotel_id, date);

-- ============================================================
-- Approval Requests
-- ============================================================
CREATE TABLE approval_requests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id      VARCHAR(30) UNIQUE NOT NULL,        -- APR_xxxx
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    approval_type   VARCHAR(20) NOT NULL,               -- STAY/RESTAURANT/TRANSFER
    reference_id    VARCHAR(50) NOT NULL,                -- hold_id or reservation_id
    details_summary TEXT,
    required_roles  TEXT[] NOT NULL,
    any_of          BOOLEAN DEFAULT false,
    status          VARCHAR(20) DEFAULT 'REQUESTED',    -- REQUESTED/APPROVED/REJECTED
    decided_by_role VARCHAR(20),
    decided_by_name VARCHAR(100),
    decided_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_approval_hotel_status ON approval_requests(hotel_id, status);

-- ============================================================
-- Payment Requests
-- ============================================================
CREATE TABLE payment_requests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id      VARCHAR(30) UNIQUE NOT NULL,        -- PAY_xxxx
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    reference_id    VARCHAR(50) NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(3) NOT NULL,
    methods         TEXT[] NOT NULL,
    due_mode        VARCHAR(10) NOT NULL,               -- NOW/SCHEDULED
    scheduled_date  DATE,
    status          VARCHAR(20) DEFAULT 'REQUESTED',    -- REQUESTED/PAID/FAILED/EXPIRED
    handled_by      VARCHAR(20) DEFAULT 'SALES',
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Tickets (Handoff)
-- ============================================================
CREATE TABLE tickets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id       VARCHAR(30) UNIQUE NOT NULL,        -- T_xxxx
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    conversation_id UUID REFERENCES conversations(id),
    reason          TEXT NOT NULL,
    transcript_summary TEXT,
    priority        VARCHAR(10) DEFAULT 'medium',
    dedupe_key      VARCHAR(200),
    status          VARCHAR(20) DEFAULT 'OPEN',         -- OPEN/IN_PROGRESS/RESOLVED/CLOSED
    assigned_to_role VARCHAR(20),
    assigned_to_name VARCHAR(100),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tickets_hotel_status ON tickets(hotel_id, status);
CREATE UNIQUE INDEX idx_tickets_dedupe ON tickets(dedupe_key) WHERE dedupe_key IS NOT NULL AND status NOT IN ('RESOLVED', 'CLOSED');

-- ============================================================
-- Notifications
-- ============================================================
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_id VARCHAR(30) UNIQUE NOT NULL,        -- N_xxxx
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    to_role         VARCHAR(20) NOT NULL,
    channel         VARCHAR(20) NOT NULL,               -- whatsapp/email/panel
    message         TEXT NOT NULL,
    metadata_json   JSONB DEFAULT '{}',
    status          VARCHAR(20) DEFAULT 'SENT',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- CRM Logs
-- ============================================================
CREATE TABLE crm_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    conversation_id UUID REFERENCES conversations(id),
    user_phone_hash VARCHAR(64),
    intent          VARCHAR(50),
    entities_json   JSONB DEFAULT '{}',
    actions         TEXT[] DEFAULT '{}',
    outcome         VARCHAR(50),
    transcript_summary TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_crm_hotel_intent ON crm_logs(hotel_id, intent, created_at DESC);

-- ============================================================
-- Restaurant Slots (capacity management)
-- ============================================================
CREATE TABLE restaurant_slots (
    id              SERIAL PRIMARY KEY,
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    date            DATE NOT NULL,
    time            TIME NOT NULL,
    area            VARCHAR(20) DEFAULT 'outdoor',
    total_capacity  INTEGER NOT NULL,
    booked_count    INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_slot_unique ON restaurant_slots(hotel_id, date, time, area);

-- ============================================================
-- Admin Users
-- ============================================================
CREATE TABLE admin_users (
    id              SERIAL PRIMARY KEY,
    hotel_id        INTEGER NOT NULL REFERENCES hotels(hotel_id),
    username        VARCHAR(100) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL,               -- ADMIN/SALES/OPS/CHEF
    display_name    VARCHAR(100),
    totp_secret     VARCHAR(64),                        -- Google Authenticator
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);
