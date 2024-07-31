# mongo_utils.py

from django.conf import settings

def get_collection(collection_name):
    return settings.mongo_db[collection_name]

def insert_document(collection_name, document):
    collection = get_collection(collection_name)
    result = collection.insert_one(document)
    return result.inserted_id

def find_documents(collection_name, query):
    collection = get_collection(collection_name)
    documents = collection.find(query)
    return [doc for doc in documents]

def update_document(collection_name, query, update_values):
    collection = get_collection(collection_name)
    result = collection.update_one(query, {'$set': update_values})
    return result.modified_count

def delete_document(collection_name, query):
    collection = get_collection(collection_name)
    result = collection.delete_one(query)
    return result.deleted_count