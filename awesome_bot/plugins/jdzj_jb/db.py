import pymongo


async def save_mongo():
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    jb_db = myclient["jdzjjb"]
    dblist = myclient.list_database_names()
    print(dblist)