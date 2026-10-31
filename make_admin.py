
from database import get_db

email = input("Enter your signup email: ").strip()

conn = get_db()

cursor = conn.execute(
    "UPDATE users SET role = 'admin' WHERE email = ?",
    (email,)
)

conn.commit()

if cursor.rowcount:
    print("User successfully promoted to Admin!")
else:
    print("Email not found. Please signup first.")

conn.close()
