CREATE TABLE clubs (
    id UUID PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    balance NUMERIC(15,2) NOT NULL
);
CREATE TABLE players (
    id UUID PRIMARY KEY,
    club_id UUID REFERENCES clubs(id),
    name VARCHAR(80) NOT NULL,
    market_value NUMERIC(15,2) NOT NULL,
    wage NUMERIC(10,2) NOT NULL,
    contract_years INT NOT NULL,
    on_loan_from UUID REFERENCES clubs(id)
);
CREATE TABLE transfer_offers (
    id UUID PRIMARY KEY,
    player_id UUID NOT NULL REFERENCES players(id),
    buyer_club_id UUID NOT NULL REFERENCES clubs(id),
    seller_club_id UUID NOT NULL REFERENCES clubs(id),
    amount NUMERIC(15,2) NOT NULL,
    counter_amount NUMERIC(15,2),
    wage NUMERIC(14,2) NOT NULL,
    contract_years INT NOT NULL,
    status VARCHAR(12) NOT NULL
);
CREATE TABLE loans (
    id UUID PRIMARY KEY,
    player_id UUID NOT NULL REFERENCES players(id),
    owner_club_id UUID NOT NULL REFERENCES clubs(id),
    borrower_club_id UUID NOT NULL REFERENCES clubs(id),
    owner_wage_share INT NOT NULL,
    may_recall BOOLEAN NOT NULL
);
