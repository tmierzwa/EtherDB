import requests
import json
from web3 import Web3

ETHERSCAN_URL = 'https://api.etherscan.io/api'
ETHERSCAN_KEY = 'RDI8SMM3K9DWAF18WHT556ARRI4FVJT76W'


# user exception classes for later use
#
class EtherscanError(Exception):
    pass


# read contract's ABI from Etherscan and parse functions and events
#
def get_abi(contract_address):

    # Dictionaries of functions and events to be returned
    functions = dict()
    events = dict()

    # Information whether the contract can be decoded
    decoded = False

    # Etherscan connection parameters
    params = dict(
        module='contract',
        action='getabi',
        address=contract_address,
        apikey=ETHERSCAN_KEY
    )

    # connect Etherscan and pass the returned message
    try:
        resp = requests.get(url=ETHERSCAN_URL, params=params).json()

        # if correct message returned pass its content
        if resp['status'] == '1' and resp['message'] == 'OK':

            abi = json.loads(resp['result'])
            decoded = True

            for item in abi:

                if 'type' in item:

                    # pass contract functions
                    if item['type'] == 'function':
                        canonical = "%s(" % item['name']
                        inputs = list()
                        for i, function_input in enumerate(item['inputs']):
                            canonical += ("%s" % function_input['type'])
                            if i < len(item['inputs']) - 1:
                                canonical += ","
                            inputs.append({"name": function_input['name'], "type": function_input['type']})
                        canonical += ")"
                        function_hash = Web3.sha3(text=canonical).hex()
                        signature = function_hash[0:10]
                        outputs = list()
                        for i, function_output in enumerate(item['outputs']):
                            outputs.append({"name": function_output['name'], "type": function_output['type']})
                        functions[signature] = dict(signature=signature,
                                                    name=item['name'],
                                                    inputs=inputs,
                                                    outputs=outputs)
                    # pass contract events
                    elif item['type'] == 'event':
                        canonical = "%s(" % item['name']
                        parameters = list()
                        for i, event_input in enumerate(item['inputs']):
                            canonical += ("%s" % event_input['type'])
                            if i < len(item['inputs']) - 1:
                                canonical += ","
                            parameters.append({"name": event_input['name'], "type": event_input['type']})
                        canonical += ")"
                        event_hash = Web3.sha3(text=canonical).hex()
                        signature = event_hash
                        events[signature] = dict(signature=signature,
                                                 name=item['name'],
                                                 parameters=parameters)

        elif resp['status'] == '0' and resp['message'] == 'NOTOK':
            if resp['result'] != 'Contract source code not verified':
                print('Etherscan response: %s' % resp['result'])
        else:
            print('Etherscan response incorrect!')

    except EtherscanError:
        print('Etherscan connection failed!')

    return decoded, functions, events


# Helper function to decode the argument value based on expected type
#
def decode_argument(raw_value, argument_type):

    if argument_type == 'address':
        decoded_value = '0x' + raw_value[-40:]
    elif argument_type in ('uint256', 'int'):
        decoded_value = int(raw_value, 16)
        if decoded_value >= 2**63:
            decoded_value = raw_value
    else:
        decoded_value = raw_value

    return decoded_value


# Decode contract transaction into a set of functions and events
#
def decode_contract_tx(tx, abi, contracts):

    # List of decoded facts (functions and events) to be returned
    facts = list()

    # Decode transaction function
    function_signature = tx['input'][:10]
    if function_signature in abi['functions']:
        function_abi = abi['functions'][function_signature]
        function_name = function_abi['name']
    else:
        function_abi = None
        function_name = function_signature

    function_arguments = dict()
    arguments = tx['input'][10:]
    for i in range(len(arguments) // 64):
        raw_value = arguments[i * 64: (i + 1) * 64]

        if function_abi:
            argument_name = function_abi['inputs'][i]['name']
            argument_type = function_abi['inputs'][i]['type']
            argument_value = decode_argument(raw_value, argument_type)
        else:
            argument_name = "Argument %d" % (i+1)
            argument_type = "unknown"
            argument_value = raw_value

        function_arguments[argument_name] = dict(type=argument_type, value=argument_value)

    facts.append(dict(contract=tx['to'],
                      time=tx['timestamp'],
                      sender=tx['from'],
                      value=float(Web3.fromWei(int(tx['value']), 'ether')),
                      cost=float(Web3.fromWei(int(tx['cost']), 'ether')),
                      type='function',
                      name=function_name,
                      arguments=function_arguments))

    # Decode transaction events
    for log in tx['logs']:

        event_address = log['address'].lower()
        event_signature = '0x' + log['topics'][0].hex()

        if event_address == tx['to'].lower():
            contract_abi = abi
        else:
            # ToDo: check for errors
            contract_abi = contracts.find({'address': event_address})[0]

        if event_signature in contract_abi['events']:
            event_abi = contract_abi['events'][event_signature]
            event_name = event_abi['name']
        else:
            event_abi = None
            event_name = event_signature

        parameters = list()
        for topic in log['topics'][1:]:
            parameters.append(topic.hex())
        data = log['data'][2:]
        for i in range(len(data) // 64):
            raw_value = data[i * 64: (i + 1) * 64]
            parameters.append(raw_value)

        # ToDo: check if this code is needed
        # if len(data) > (i+1)*64:
        #     raw_value = data[(i + 1) * 64:]
        #     event_parameters.append(raw_value)

        event_parameters = dict()
        for i, parameter in enumerate(parameters):

            if event_abi:
                parameter_name = event_abi['parameters'][i]['name']
                parameter_type = event_abi['parameters'][i]['type']
                parameter_value = decode_argument(parameter, parameter_type)
            else:
                parameter_name = "Parameter %d" % (i + 1)
                parameter_type = "unknown"
                parameter_value = parameter

            event_parameters[parameter_name] = dict(type=parameter_type, value=parameter_value)

        facts.append(dict(contract=tx['to'],
                          time=tx['timestamp'],
                          sender=tx['from'],
                          value=0,
                          cost=0,
                          type='event',
                          name=event_name,
                          arguments=event_parameters))

    return facts
