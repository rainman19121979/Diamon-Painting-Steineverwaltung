"""
Database module for Diamond Painting Organizer
Handles SQLite database operations
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager

# Database file path
DB_PATH = Path(__file__).parent.parent / 'data' / 'stones.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with schema"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dmc_number TEXT NOT NULL,
                color_name TEXT NOT NULL,
                color_hex TEXT,
                quantity TEXT,
                pieces INTEGER,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster searches
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dmc_number ON stones(dmc_number)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_color_name ON stones(color_name)
        """)

        conn.commit()

def migrate_from_json():
    """Migrate data from JSON file to SQLite"""
    json_path = Path(__file__).parent.parent / 'data' / 'stones.json'

    if not json_path.exists():
        return 0

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            stones = json.load(f)

        if not stones:
            return 0

        with get_db() as conn:
            # Check if data already exists
            cursor = conn.execute("SELECT COUNT(*) FROM stones")
            if cursor.fetchone()[0] > 0:
                return 0  # Already migrated

            # Insert all stones
            for stone in stones:
                conn.execute("""
                    INSERT INTO stones (id, dmc_number, color_name, color_hex, quantity, pieces, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    stone.get('id'),
                    stone.get('dmc_number'),
                    stone.get('color_name'),
                    stone.get('color_hex'),
                    stone.get('quantity'),
                    stone.get('pieces'),
                    stone.get('location')
                ))

            conn.commit()

            # Backup old JSON file
            backup_path = json_path.with_suffix('.json.backup')
            json_path.rename(backup_path)

            return len(stones)

    except Exception as e:
        print(f"Migration error: {e}")
        return 0

def get_all_stones() -> List[Dict]:
    """Get all stones from database"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT id, dmc_number, color_name, color_hex, quantity, pieces, location
            FROM stones
            ORDER BY id
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_stone(stone_id: int) -> Optional[Dict]:
    """Get a single stone by ID"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT id, dmc_number, color_name, color_hex, quantity, pieces, location
            FROM stones
            WHERE id = ?
        """, (stone_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_stone(stone_data: Dict) -> int:
    """Add a new stone to database"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO stones (dmc_number, color_name, color_hex, quantity, pieces, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            stone_data.get('dmc_number'),
            stone_data.get('color_name'),
            stone_data.get('color_hex'),
            stone_data.get('quantity'),
            stone_data.get('pieces'),
            stone_data.get('location')
        ))
        conn.commit()
        return cursor.lastrowid

def update_stone(stone_id: int, stone_data: Dict) -> bool:
    """Update an existing stone"""
    with get_db() as conn:
        conn.execute("""
            UPDATE stones
            SET dmc_number = ?,
                color_name = ?,
                color_hex = ?,
                quantity = ?,
                pieces = ?,
                location = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            stone_data.get('dmc_number'),
            stone_data.get('color_name'),
            stone_data.get('color_hex'),
            stone_data.get('quantity'),
            stone_data.get('pieces'),
            stone_data.get('location'),
            stone_id
        ))
        conn.commit()
        return conn.total_changes > 0

def delete_stone(stone_id: int) -> bool:
    """Delete a stone from database"""
    with get_db() as conn:
        conn.execute("DELETE FROM stones WHERE id = ?", (stone_id,))
        conn.commit()
        return conn.total_changes > 0

def search_stones(query: str) -> List[Dict]:
    """Search stones by DMC number or color name"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT id, dmc_number, color_name, color_hex, quantity, pieces, location
            FROM stones
            WHERE dmc_number LIKE ? OR color_name LIKE ?
            ORDER BY dmc_number
        """, (f'%{query}%', f'%{query}%'))
        return [dict(row) for row in cursor.fetchall()]

def export_to_json() -> str:
    """Export all stones to JSON format"""
    stones = get_all_stones()
    return json.dumps(stones, ensure_ascii=False, indent=2)

def import_from_json(json_data: str) -> int:
    """Import stones from JSON data"""
    try:
        stones = json.loads(json_data)

        with get_db() as conn:
            # Clear existing data
            conn.execute("DELETE FROM stones")

            # Insert imported data
            for stone in stones:
                conn.execute("""
                    INSERT INTO stones (dmc_number, color_name, color_hex, quantity, pieces, location)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    stone.get('dmc_number'),
                    stone.get('color_name'),
                    stone.get('color_hex'),
                    stone.get('quantity'),
                    stone.get('pieces'),
                    stone.get('location')
                ))

            conn.commit()
            return len(stones)

    except Exception as e:
        print(f"Import error: {e}")
        return 0
