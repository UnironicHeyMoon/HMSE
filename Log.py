import sqlite3
from Database import Database
from User import User


class Log:
    def __init__(self, filename : str, database : Database) -> None:
        self.database = database
        self._con = sqlite3.connect(filename)
        with open('setup_logging_database.sql') as sql_file:
            self._con.executescript(sql_file.read())
        
    def commit(self):
        self.con.commit()

    def close(self):
        self.con.close()

    def rollback(self):
        self.con.rollback()
    
    @property
    def con(self) -> sqlite3.Connection:
        return self._con

    @property
    def cursor(self) -> sqlite3.Cursor:
        return self.con.cursor()
    

    def unpack_nested_tuple(self, my_tuple):
        if (len(my_tuple) != 1 or type(my_tuple[0]) is not tuple):
            return (my_tuple)
        else:
            return self.unpack_nested_tuple(my_tuple[0])

    def run_command(self, command, *args):
        return self.cursor.execute(command, self.unpack_nested_tuple(args))


    def add_log_message(self, the_class : str, message_type : str, message : str, user : User = None):
        try:
            user_id = user.id if user is not None else 0
        except:
            user_id = 0
            message+="(User id getting failed...)"
        time_id = self.database.get_current_time_id()

        self.run_command('''INSERT INTO log
            (
                user_id,
                time_id,
                class,
                message_type,
                message
            ) VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?
            )''', user_id, time_id, the_class, message_type, message)
        self.commit()

class LogMessageType:
    EXCEPTION = "EXCEPTION"
    UPDATE = "UPDATE"
    PROCESS = "PROCESS"
    PROCESS_NOTIFICATION = "PROCESS_NOTIFICATION"
    PLACE_BUY_COMMANDS = "PLACE_BUY_COMMANDS"
    PLACE_SELL_COMMANDS = "PLACE_SELL_COMMANDS"
    CANCEL_COMMANDS = "CANCEL_COMMANDS"
    MALFORMED = "MALFORMED"
    JEWRY = "JEWRY"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    COMPLETED_SALE = "COMPLETED_SALE"
    FAILED_SALE = "FAILED_SALE"
    EXPIRED = "EXPIRED"
    BANK = "BANK"