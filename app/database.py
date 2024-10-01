from databases import Database

postgres_url = "postgresql://root:postges@139.144.63.238/mapaction"
# postgres_url = "postgresql://postgres:postges@localhost/mapaction"
database = Database(postgres_url)
