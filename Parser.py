
class Parser:
    def parse_message(self, message : str):
        if ("#demo" in message):
            return {
                "type": "DEMO"
            }


        to_return = {}  
        try:
            tokens = message.upper().split(" ")
            starting_index = tokens.index("@HMSE")
            parameters = tokens[starting_index:]
            named_parameters = {}
            for parameter in parameters:
                if "=" in parameter:
                    key = parameter.split("=")[0].upper()
                    value = parameter.split("=")[1].upper()
                    named_parameters[key] = value
            print(parameters, named_parameters)

            command_name = parameters[1]
            if (command_name.upper() == "BUY"):
                to_return['type'] = 'BUY'
                to_return['asset'] = parameters[2]
                to_return['max_price'] = parameters[3]
                to_return['time_remaining'] = named_parameters['TIME'] if 'TIME' in named_parameters else 1
                to_return['count'] = named_parameters['COUNT'] if 'COUNT' in named_parameters else 1
            elif (command_name.upper() == "SELL"):
                to_return['type'] = 'SELL'
                to_return['asset'] = parameters[2]
                to_return['price'] = parameters[3]
                to_return['time_remaining'] = named_parameters['time'] if 'time' in named_parameters else 1
                to_return['count'] = named_parameters['count'] if 'count' in named_parameters else 1
            
            elif (command_name.upper() == "CANCEL"):
                to_return['type'] = 'CANCEL'
                to_return['asset'] = parameters[2]            
            elif (command_name.upper() == "MARKET"):
                to_return['type'] = 'MARKET'
                to_return['asset'] = parameters[2]            
            elif (command_name.upper() == "BALANCE"):
                to_return['type'] = "BALANCE"
            elif (command_name.upper() == "WITHDRAW"):
                to_return['type'] = "WITHDRAW"
                to_return['amount'] = parameters[2]
            elif (command_name.upper() == "TICKER"):
                to_return['type'] = "TICKER"
            elif (command_name.upper() == "TREND"):
                to_return['type'] = "TREND"
                to_return['asset'] = parameters[2]
            elif (command_name.upper() == "RANDSEY"):
                to_return['type'] = "RANDSEY"
            else:
                to_return['type'] = "UNKNOWN"
                to_return["unrecognized_command"] = parameters[1]
        except BaseException as e:
            to_return['type'] = "MALFORMED"
            to_return['exception'] = str(e)
        return to_return