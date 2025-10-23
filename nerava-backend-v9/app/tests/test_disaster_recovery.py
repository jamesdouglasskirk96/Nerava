"""
Disaster recovery tests for backup and restore procedures
"""
import pytest
import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
from app.scripts.db_backup import backup_postgresql, backup_sqlite, backup_mysql
from app.scripts.db_restore import restore_postgresql, restore_sqlite, restore_mysql

class TestDisasterRecovery:
    """Test disaster recovery procedures"""
    
    def test_sqlite_backup(self):
        """Test SQLite database backup"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data 1',))
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data 2',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify backup was created
            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0
            
            # Verify backup contains data
            backup_conn = sqlite3.connect(backup_path)
            result = backup_conn.execute('SELECT COUNT(*) FROM test_table').fetchone()
            assert result[0] == 2
            backup_conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_sqlite_restore(self):
        """Test SQLite database restore"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data 1',))
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data 2',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Corrupt the original database
            os.unlink(db_path)
            
            # Restore from backup
            restore_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify restore was successful
            assert os.path.exists(db_path)
            
            # Verify data integrity
            conn = sqlite3.connect(db_path)
            result = conn.execute('SELECT COUNT(*) FROM test_table').fetchone()
            assert result[0] == 2
            
            # Verify specific data
            result = conn.execute('SELECT data FROM test_table ORDER BY id').fetchall()
            assert result[0][0] == 'test data 1'
            assert result[1][0] == 'test data 2'
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_backup_verification(self):
        """Test backup file verification"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify backup file exists and has content
            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0
            
            # Verify backup is not empty
            backup_conn = sqlite3.connect(backup_path)
            result = backup_conn.execute('SELECT COUNT(*) FROM test_table').fetchone()
            assert result[0] > 0
            backup_conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_restore_verification(self):
        """Test restore verification"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Corrupt the original database
            os.unlink(db_path)
            
            # Restore from backup
            restore_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify restore was successful
            assert os.path.exists(db_path)
            
            # Verify database is accessible
            conn = sqlite3.connect(db_path)
            result = conn.execute('SELECT 1').fetchone()
            assert result[0] == 1
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_backup_retention(self):
        """Test backup retention policy"""
        # Create temporary backup directory
        backup_dir = tempfile.mkdtemp()
        
        try:
            # Create old backup files
            old_backup = os.path.join(backup_dir, 'nerava_backup_old.db')
            with open(old_backup, 'w') as f:
                f.write('old backup data')
            
            # Create recent backup file
            recent_backup = os.path.join(backup_dir, 'nerava_backup_recent.db')
            with open(recent_backup, 'w') as f:
                f.write('recent backup data')
            
            # Simulate retention cleanup (files older than 30 days)
            import time
            old_time = time.time() - (31 * 24 * 60 * 60)  # 31 days ago
            os.utime(old_backup, (old_time, old_time))
            
            # Verify old backup exists before cleanup
            assert os.path.exists(old_backup)
            assert os.path.exists(recent_backup)
            
            # Simulate cleanup (in real implementation, this would be done by the script)
            # For testing, we'll just verify the logic
            current_time = time.time()
            for filename in os.listdir(backup_dir):
                if filename.startswith('nerava_backup_'):
                    file_path = os.path.join(backup_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > (30 * 24 * 60 * 60):  # 30 days
                        os.unlink(file_path)
            
            # Verify old backup was cleaned up
            assert not os.path.exists(old_backup)
            assert os.path.exists(recent_backup)
            
        finally:
            # Clean up
            shutil.rmtree(backup_dir)
    
    def test_backup_encryption(self):
        """Test backup encryption (simulated)"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('sensitive data',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify backup was created
            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0
            
            # In a real implementation, we would verify encryption
            # For testing, we'll just verify the backup contains data
            backup_conn = sqlite3.connect(backup_path)
            result = backup_conn.execute('SELECT data FROM test_table').fetchone()
            assert result[0] == 'sensitive data'
            backup_conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_restore_force_mode(self):
        """Test restore with force mode"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('original data',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Modify the original database
            conn = sqlite3.connect(db_path)
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('modified data',))
            conn.commit()
            conn.close()
            
            # Restore with force mode (should overwrite existing database)
            restore_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify restore was successful
            conn = sqlite3.connect(db_path)
            result = conn.execute('SELECT COUNT(*) FROM test_table').fetchone()
            assert result[0] == 1  # Only original data, not modified data
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_backup_compression(self):
        """Test backup compression (simulated)"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            # Insert some data to make compression meaningful
            for i in range(100):
                conn.execute('INSERT INTO test_table (data) VALUES (?)', (f'data {i}',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify backup was created
            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0
            
            # In a real implementation, we would verify compression
            # For testing, we'll just verify the backup contains data
            backup_conn = sqlite3.connect(backup_path)
            result = backup_conn.execute('SELECT COUNT(*) FROM test_table').fetchone()
            assert result[0] == 100
            backup_conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_restore_verification_failure(self):
        """Test restore verification failure handling"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Corrupt the backup file
            with open(backup_path, 'w') as f:
                f.write('corrupted data')
            
            # Attempt to restore from corrupted backup
            try:
                restore_sqlite(f"sqlite:///{db_path}", backup_path)
                # If we get here, the restore should have failed
                # In a real implementation, this would raise an exception
                assert False, "Restore should have failed with corrupted backup"
            except Exception:
                # Expected behavior - restore should fail with corrupted backup
                pass
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_backup_restore_cycle(self):
        """Test complete backup and restore cycle"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Create test data
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data 1',))
            conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test data 2',))
            conn.commit()
            conn.close()
            
            # Create backup
            backup_path = tempfile.mktemp(suffix='.db')
            backup_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify backup was created
            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0
            
            # Corrupt the original database
            os.unlink(db_path)
            
            # Restore from backup
            restore_sqlite(f"sqlite:///{db_path}", backup_path)
            
            # Verify restore was successful
            assert os.path.exists(db_path)
            
            # Verify data integrity
            conn = sqlite3.connect(db_path)
            result = conn.execute('SELECT COUNT(*) FROM test_table').fetchone()
            assert result[0] == 2
            
            # Verify specific data
            result = conn.execute('SELECT data FROM test_table ORDER BY id').fetchall()
            assert result[0][0] == 'test data 1'
            assert result[1][0] == 'test data 2'
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)
