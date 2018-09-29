import requests
import json
from database import connect_database


# Scrap address nickname form CK API
#
def scrap_profile(address):

    link = 'https://api.cryptokitties.co/user/%s' % address
    page = requests.get(link)
    if page:
        nickname = json.loads(page.text)['nickname']
    else:
        nickname = address

    return {'nickname': nickname}


# Scrap kitty attributes form CK API
#
def scrap_kitty(cat_id):

    link = 'https://api.cryptokitties.co/kitties/%s' % cat_id
    page = requests.get(link)
    attributes = dict()
    if page:
        page_dict = json.loads(page.text)
        generation = page_dict['generation']
        attributes['generation'] = generation
        attrs = page_dict['enhanced_cattributes']
        for attribute in attrs:
            attributes[attribute['type']] = attribute['description']

    return attributes


# Generate Contract Application Interface file
#
def generate_cai(cai_file):

    cai = {
      "address": "0x06012c8cf97BEaD5deAe237070F9587f8E7A266d",
      "name": "CryptoKitties",
      "cubes": [
        {
          "name": "Births",
          "fact_type": "event",
          "fact_name": "Birth",
          "dimensions": [
            {
              "name": "time",
              "field": "time",
              "decode_time": [
                "year",
                "month",
                "dow",
                "hour"
              ]
            },
            {
              "name": "owner",
              "field": "arguments.owner",
              "off_chain_details": "nicknames"
            },
            {
              "name": "sire",
              "field": "arguments.sireId",
              "off_chain_details": "kitties"
            },
            {
              "name": "matron",
              "field": "arguments.matronId",
              "off_chain_details": "kitties"
            },
            {
              "name": "kitty",
              "field": "arguments.kittyId",
              "off_chain_details": "kitties"
            }
          ],
          "measures": [
            {
              "name": "number",
              "value": "1"
            }
          ]
        },
        {
          "name": "Transfers",
          "fact_type": "event",
          "fact_name": "Transfer",
          "dimensions": [
            {
              "name": "time",
              "field": "time",
              "decode_time": [
                "year",
                "month",
                "dow",
                "hour"
              ]
            },
            {
              "name": "sender",
              "field": "arguments.from",
              "off_chain_details": "nicknames"
            },
            {
              "name": "receiver",
              "field": "arguments.to",
              "off_chain_details": "nicknames"
            },
            {
              "name": "kitty",
              "field": "arguments.tokenId",
              "off_chain_details": "kitties"
            }
          ],
          "measures": [
            {
              "name": "number",
              "value": "1"
            },
            {
              "name": "cost",
              "value": "fact['cost']"
            }
          ]
        }
      ],
    }

    ethdb = connect_database()
    db_kitties = ethdb.CryptoKitties_kitties
    db_nicknames = ethdb.CryptoKitties_nicknames

    kitties_dict = dict()
    kitties = db_kitties.find()
    for kitty in kitties:
        kitty_id = kitty.pop('id')
        kitty.pop('_id')
        kitties_dict[kitty_id] = kitty

    cai['kitties'] = kitties_dict

    nicknames_dict = dict()
    nicknames = db_nicknames.find()
    for nickname in nicknames:
        nickname_id = nickname.pop('id')
        nickname.pop('_id')
        if nickname['nickname'] != '':
            nicknames_dict[nickname_id] = nickname

    cai['nicknames'] = nicknames_dict

    with open(cai_file, 'w') as f:
        json.dump(cai, f, indent=2)
        f.close()

    return


# main loop
#
ethdb = connect_database()
db_births = ethdb.CryptoKitties_Births
db_kitties = ethdb.CryptoKitties_kitties
db_nicknames = ethdb.CryptoKitties_nicknames

# scrap data for already born kitties
kitties = db_births.find().distinct('kitty')
for kitty_id in kitties:

    kitty_data = dict()
    kitty_data['id'] = kitty_id
    kitty_data.update(scrap_kitty(kitty_id))
    db_kitties.insert_one(kitty_data)

    print(kitty_id, kitty_data)

# scrap data for kitties owners
owners = db_births.find().distinct('owner')
for owner_id in owners:
    owner_data = dict()
    owner_data['id'] = owner_id
    owner_data.update(scrap_profile(owner_id))
    db_nicknames.insert_one(owner_data)

    print(owner_id, owner_data)

# generate final CAI file
generate_cai('kitties.json')
