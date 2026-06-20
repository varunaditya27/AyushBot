# Reference Data Formats

These files contain no real patient data. Copy the example templates to
`villages.json` and `facilities.csv`, then replace every example record with
approved local reference data.

## Villages

Accepted formats: JSON or CSV. JSON may be an array directly or an object with
a `records` array.

Required fields:

- `id`: stable unique identifier, maximum 64 characters.
- `name`: display name.

Optional fields:

- `district`, `state`, `pincode`
- `latitude`: decimal degrees from `-90` to `90`.
- `longitude`: decimal degrees from `-180` to `180`.
- `active`: boolean, defaults to `true`.
- `metadata_json`: JSON object. In CSV, encode it as a JSON string.

## Facilities

Accepted formats: CSV or JSON.

Required fields:

- `id`: stable unique identifier, maximum 64 characters.
- `name`: facility display name.
- `type`: one of `SC`, `PHC`, `CHC`, `SDH`, `DH`, `OTHER`.
- `latitude`, `longitude`: decimal degrees.

Optional fields:

- `village_id`: must match a village already present in the same database.
- `address`, `phone`
- `active`: boolean, defaults to `true`.
- `metadata_json`: JSON object. In CSV, encode it as a JSON string.

## Commands

```bash
cp data/reference/villages.example.json data/reference/villages.json
cp data/reference/facilities.example.csv data/reference/facilities.csv
make migrate-db
make seed-db
```

Seeding validates every record before commit and upserts by stable `id`. If any
record is invalid, the transaction is rolled back.
