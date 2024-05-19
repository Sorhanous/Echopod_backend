import psycopg2

# Connect to your postgres DB
conn = psycopg2.connect(
    dbname="Bevi_DB",
    user="postgres",
    password="your_password",
    host="localhost"
)

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a query
cur.execute("SELECT * FROM users")

# Retrieve query results
records = cur.fetchall()

print(records)

# Close the cursor and connection
cur.close()
conn.close()