import sqlite3
from Database import Database
from User import User
from os.path import exists
from os.path import exists, join, realpath

from Util import get_real_filename

'''
Writes messages to the log
'''
class Log:
    def __init__(self, filename : str, database : Database) -> None:
        self.database = database
        self._con = sqlite3.connect(get_real_filename(filename), timeout=120)
        with open(get_real_filename("setup_logging_database.sql")) as sql_file:
            self._con.executescript(sql_file.read())
        
    def commit(self):
        self.con.commit()

    def close(self):
        self.commit()
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
    
    def get_rows(self, command, *args):
        return self.run_command(command, args).fetchall()
    
    def get_only_row(self, command, *args):
        to_return = self.run_command(command, args).fetchone()
        return to_return
    
    def get_only_cell(self, command, *args):
        row = self.get_only_row(command, args)
        if (row is None):
            return None
        assert (len(row) == 1)
        return row[0]


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

    def get_log_messages(self, type : str):
        rows = self.get_rows('''
            SELECT
                    user_id,
                    time_id,
                    class,
                    message_type,
                    message
            FROM log
            WHERE message_type = ?
            ''', type)
        
        to_return = []

        for row in rows:
            user_id, time_id, class_, message_type, message = row
            to_return.append(
                {
                    'user_id': user_id,
                    'time_id': time_id,
                    'class': class_,
                    'message_type': message_type,
                    'message': message
                }
            )
        return to_return

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