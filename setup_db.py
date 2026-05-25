import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS skin_cancer_db")
    cursor.execute("USE skin_cancer_db")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50),
        password VARCHAR(50)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        age INT,
        result VARCHAR(20),
        probability FLOAT,
        image_path VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
        db.commit()
    
    print("Database setup successful")
except Exception as e:
    print(f"Error: {e}")
