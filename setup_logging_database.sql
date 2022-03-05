CREATE TABLE IF NOT EXISTS log (
    log_id integer PRIMARY KEY,
    user_id integer,
    time_id integer,
    class string,
    message_type string,
    message string
)
