--SCHEMA ONLY! NO INSERTS OR THERE WILL BE FUCKING PROBLEMS!

--Contains assets owned for users
--Key is composite. 
--Amount is the number of assets they can sell right now
--Amount_in_escrow is the number of assets they have listed
CREATE TABLE IF NOT EXISTS owned_assets
    (user_id integer,
    asset_id integer,
    amount integer,
    amount_in_escrow integer,
    PRIMARY KEY (user_id, asset_id));

--The assets
CREATE TABLE IF NOT EXISTS assets (
    asset_id integer PRIMARY KEY,
    name string);

--The commands
--If type is...
-- - 0, it is a BUY command
--  - amount is the listing price
--  - asset_id is the asset to list
-- - 1, it is a SELL command
--  - amount is the max price
--  - asset_id is the asset to buy
CREATE TABLE IF NOT EXISTS commands (
    command_id integer PRIMARY KEY,
    user_id integer,
    command_type integer,
    amount integer,
    asset_id integer,
    expiring_in integer);

--Stores all users, and their names, and potentially more information if needed
--Note about user_name: This should be updated every time a new piece of correspondence arrives with the username on it
--Based Aevann :marseykneel:
CREATE TABLE IF NOT EXISTS users (
    user_id integer PRIMARY KEY,
    user_name string,
    balance integer,
    balance_in_escrow integer
);

CREATE TABLE IF NOT EXISTS prices (
    time_id integer,
    asset_id integer,
    price integer,
    day_average_price integer,
    week_average_price integer,
    month_average_price integer,
    PRIMARY KEY (time_id, asset_id)
);

--Various information about the state of the system.
CREATE TABLE IF NOT EXISTS state (
    id integer PRIMARY KEY,
    last_processed_notification_id integer,
    current_time_id integer
);