```
topic: MongoDB
tool: mongoimport
category: Database Administration
examples: [JSON, JSON Array, CSV, Upsert]
```

`mongoimport` is a command-line utility included with MongoDB Database Tools. It imports JSON, CSV, and TSV files into MongoDB collections.

Important: Run `mongoimport` from your Linux/macOS terminal, not inside `mongosh`.

## 1. Import a JSON file (one document per line)

Suppose `students.json` contains:

```
{"_id": 1, "name": "Alice", "major": "CS", "gpa": 3.8}
{"_id": 2, "name": "Bob", "major": "Math", "gpa": 3.5}
{"_id": 3, "name": "Carol", "major": "CS", "gpa": 3.9}
```

Run:

```
mongoimport \
  --db university \
  --collection students \
  --file students.json
```

This imports all three documents into `university.students`.

## 2. Import a JSON array

If the JSON file contains a single array:

```
[
  {"name": "Alice", "major": "CS"},
  {"name": "Bob", "major": "Math"},
  {"name": "Carol", "major": "CS"}
]
```

Use `--jsonArray`:

```
mongoimport \
  --db university \
  --collection students \
  --file students.json \
  --jsonArray
```

Without `--jsonArray`, MongoDB won't interpret this format correctly.

## 3. Import a CSV file

Suppose `students.csv` contains:

```
name,major,gpa
Alice,CS,3.8
Bob,Math,3.5
Carol,CS,3.9
```

Run:

```
mongoimport \
  --db university \
  --collection students \
  --type csv \
  --headerline \
  --file students.csv
```

The `--headerline` option tells MongoDB to use the first row as field names.

Watch out: CSV fields may be imported as strings. Use `--columnsHaveTypes` with typed headers when you need explicit numeric types.

## 4. Replace an existing collection

If you want to start fresh each time:

```
mongoimport \
  --db university \
  --collection students \
  --file students.json \
  --drop
```

The `--drop` option deletes the existing collection before importing the new data, including its indexes.

## 5. Update existing documents (upsert)

Suppose you have an updated `students.json` containing existing and new students.

```
mongoimport \
  --db university \
  --collection students \
  --file students.json \
  --mode upsert \
  --upsertFields _id
```

This will update documents matching `_id` and insert documents that don't already exist.

## 6. Import into a remote MongoDB server

```
mongoimport \
  --uri "mongodb://localhost:27017" \
  --db university \
  --collection students \
  --file students.json
```

For an authenticated server:

```
mongoimport \
  --uri "mongodb://username@server.example.com:27017/university?authSource=admin" \
  --collection students \
  --file students.json \
  --password
```

The password prompt avoids putting the password directly into shell history.

## Quick reference

| Option           | Purpose                                      |
| ---------------- | -------------------------------------------- |
| `--db`           | Database name                                |
| `--collection`   | Collection name                              |
| `--file`         | Input file                                   |
| `--type csv`     | Import CSV                                   |
| `--headerline`   | Use CSV headers as field names               |
| `--jsonArray`    | Import a JSON array                          |
| `--drop`         | Delete existing collection before importing  |
| `--mode upsert`  | Update matching documents or insert new ones |
| `--upsertFields` | Specify fields used to match documents       |
| `--uri`          | MongoDB connection string                    |

### Verify the import in mongosh

```
use university

db.students.countDocuments({})

db.students.find().pretty()

db.students.find({major: "CS"})
```

One useful teaching distinction: `mongoimport` is not the same as `mongorestore`. `mongoimport` loads JSON/CSV/TSV data, while `mongorestore` restores BSON database dumps produced by `mongodump`.