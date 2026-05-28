from database import get_connection

SUPPLIERS = [
    ("Samsung", "South Korea", "Electronics"),
    ("TSMC", "Taiwan", "Semiconductors"),
    ("Tesla", "USA", "Automotive"),
    ("Foxconn", "Taiwan", "Electronics"),
    ("BASF", "Germany", "Chemicals"),
]

def seed():
    conn = get_connection()
    cursor = conn.cursor()

    for name, country, sector in SUPPLIERS:
        cursor.execute("""
            INSERT INTO suppliers (name, country, sector)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (name, country, sector))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✓ {len(SUPPLIERS)} fournisseurs seedés")

if __name__ == "__main__":
    seed()