#


### Connect to the MongoDB container:

`docker exec -it mongodb mongo -u root -p root`


### Once connected, switch to a specific database (replace 'your_database' with the actual database name):

`use your_database`

### List all collections in the current database:

`show collections`

### To view documents in a specific collection (replace 'your_collection' with the actual collection name):

`db.your_collection.find()`