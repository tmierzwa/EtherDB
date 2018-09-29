import json
from pymongo import collection
from database import connect_database
from contract import decode_contract_tx


# user exception classes for later use
#
class JSONParseError(Exception):
    def __init__(self):
        pass


# parse contract transactions into facts
#
def parse_contract(contract_address, contract_name):

    ethdb = connect_database()
    db_contracts = ethdb.contracts
    db_transactions = ethdb.transactions

    db_facts = collection.Collection(ethdb, "%s_facts" % contract_name)
    db_facts.drop()

    contract_abi = db_contracts.find({'address': contract_address})[0]
    contract_txs = db_transactions.find({'to': contract_address})

    for i, tx in enumerate(contract_txs):

        if not i % 100:
            print('.', end='', flush=True)
        if not i % 1000:
            print(i)

        contract_facts = decode_contract_tx(tx, contract_abi, db_contracts)
        for fact in contract_facts:
            db_facts.insert_one(fact)

    return


# read and parse JSON file with CAI
#
def read_cai(cai_file):

    cai = None

    try:
        f = open(cai_file)
    except FileNotFoundError:
        print("CAI file %s not found." % cai_file)
        return cai

    try:
        cai = json.load(f)
    except JSONParseError:
        print("CAI file %s parse error." % cai_file)

    f.close()
    return cai


# create analytical cube based on facts and CAI
#
def create_cube(cai):

    ethdb = connect_database()
    db_facts = collection.Collection(ethdb, "%s_facts" % cai['name'])

    for cube in cai['cubes']:
        print('Generating: %s cube...' % cube['name'])
        cube_facts = db_facts.find({"contract": cai['address'], "type": cube['fact_type'], "name": cube['fact_name']})
        db_cube = collection.Collection(ethdb, '%s_%s' % (cai['name'], cube['name']))
        db_cube.drop()

        for fact in cube_facts:
            record = dict()
            for dimension in cube['dimensions']:
                if dimension['field'][:9] == "arguments":
                    if dimension['field'][10:] in fact['arguments']:
                        record[dimension['name']] = fact['arguments'][dimension['field'][10:]]['value']
                else:
                    if dimension['field'] in fact:
                        record[dimension['name']] = fact[dimension['field']]
                if 'off_chain_details' in dimension:
                    if dimension['off_chain_details'] in cai:
                        if str(record[dimension['name']]) in cai[dimension['off_chain_details']]:
                            oc_dim_attributes = dict()
                            oc_details = cai[dimension['off_chain_details']][str(record[dimension['name']])]
                            for key in oc_details:
                                oc_dim_attributes['%s %s [OC]' % (dimension['name'], key)] = oc_details[key]
                            record.update(oc_dim_attributes)

            for measure in cube['measures']:
                try:
                    value = eval(measure['value'])
                    record[measure['name']] = value
                except SyntaxError:
                    pass

            if len(record) > 0:
                db_cube.insert_one(record)

    return


kitties_cai = read_cai('kitties.cai')
create_cube(kitties_cai)
