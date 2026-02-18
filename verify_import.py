import sys
import os

print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    print("Attempting to import database.database...")
    import database.database
    print(f"Successfully imported database.database: {database.database}")
    from database.database import Database
    print(f"Successfully imported Database class: {Database}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
