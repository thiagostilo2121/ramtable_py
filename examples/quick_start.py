from ramtable import Table

people = Table(
    name="people",
    columns={
        "id": int,
        "name": str,
        "age": int,
        "email": str,
    },
)

people.rows.insert(
    {"id": 1, "name": "Ada", "age": 36, "email": "ada@example.com"}
)
people.rows.insert(
    {"id": 2, "name": "Linus", "age": 28, "email": "linus@example.com"}
)

print(people.rows.get_column("name"))

updated = people.rows.update(
    where={"id": 1},
    values={"name": "Ada Lovelace"},
)
print(updated)

print(people.rows.get_one(0))

older = people.rows.filter({"age": {">": 30}})
print([row["name"] for row in older])
