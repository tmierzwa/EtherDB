from pymongo import MongoClient

mongo = MongoClient(host='localhost', port=27017)
terms = mongo.cdo.terms
terms.insert_one({'term': 'customer', 'description': 'Ala druga', 'classes': [1, 2, 3]})
print (terms.count())
