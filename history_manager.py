import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import mysql.connector
from mysql.connector import Error
import logging

logger = logging.getLogger(__name__)

class HistoryManager:
    """Manages the history of email extraction results using MySQL database"""
    
    def __init__(self, 
                 host: str = None,
                 database: str = None,
                 user: str = None,
                 password: str = None,
                 port: int = 3306):
        """
        Initialize the HistoryManager with MySQL connection
        
        Args:
            host (str): MySQL server host (default: from environment or 'localhost')
            database (str): Database name (default: from environment or 'email_extractor')
            user (str): MySQL username (default: from environment or 'root')
            password (str): MySQL password (default: from environment or '')
            port (int): MySQL port (default: 3306)
        """
        # Get database credentials from environment variables or use defaults
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.database = database or os.getenv('DB_NAME', 'email_extractor')
        self.user = user or os.getenv('DB_USER', 'root')
        self.password = password or os.getenv('DB_PASSWORD', '')
        self.port = port or int(os.getenv('DB_PORT', '3306'))
        
        self.connection = None
        self.ensure_database_exists()
        self.ensure_tables_exist()
    
    def get_connection(self):
        """Get MySQL database connection"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    port=self.port,
                    autocommit=False
                )
            return self.connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise
    
    def ensure_database_exists(self):
        """Create database if it doesn't exist"""
        try:
            # Connect without specifying database
            temp_conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port
            )
            cursor = temp_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            temp_conn.close()
            logger.info(f"Database '{self.database}' ensured")
        except Error as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create extractions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extractions (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    input_method VARCHAR(50) NOT NULL,
                    total_urls INT NOT NULL,
                    processing_time DECIMAL(10, 2) NOT NULL,
                    total_emails_found INT NOT NULL,
                    successful_extractions INT NOT NULL,
                    failed_extractions INT NOT NULL,
                    urls_processed TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_name (name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Create extraction_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extraction_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    extraction_id VARCHAR(255) NOT NULL,
                    website_url TEXT NOT NULL,
                    email_1 VARCHAR(255),
                    email_2 VARCHAR(255),
                    email_3 VARCHAR(255),
                    email_4 VARCHAR(255),
                    email_5 VARCHAR(255),
                    source_pages TEXT,
                    contact_form_found BOOLEAN DEFAULT FALSE,
                    status TEXT,
                    pages_crawled INT DEFAULT 0,
                    FOREIGN KEY (extraction_id) REFERENCES extractions(id) ON DELETE CASCADE,
                    INDEX idx_extraction_id (extraction_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            conn.commit()
            cursor.close()
            logger.info("Tables ensured")
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            if conn:
                conn.rollback()
            raise
    
    def save_extraction(self, urls: List[str], results: List[Dict], processing_time: float, input_method: str = "text", name: str = None):
        """
        Save extraction results to database
        
        Args:
            urls (List[str]): List of URLs that were processed
            results (List[Dict]): List of extraction results
            processing_time (float): Time taken to process
            input_method (str): Method used ('text' or 'csv')
            name (str): Name of the extraction (CSV filename or "Extraction X")
        
        Returns:
            str: ID of the saved extraction
        """
        conn = None
        cursor = None
        
        try:
            # If no name provided, generate one based on history count
            if name is None:
                history = self.load_history()
                extraction_num = len(history) + 1
                name = f"Extraction {extraction_num}"
            
            # Generate extraction ID
            extraction_id = f"extraction_{int(datetime.now().timestamp() * 1000)}"
            timestamp = datetime.now()
            
            # Calculate statistics
            total_emails_found = sum(len(r.get('emails', [])) for r in results)
            successful_extractions = sum(1 for r in results if r.get('emails'))
            failed_extractions = sum(1 for r in results if not r.get('emails'))
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Insert extraction record
            cursor.execute("""
                INSERT INTO extractions 
                (id, name, timestamp, input_method, total_urls, processing_time, 
                 total_emails_found, successful_extractions, failed_extractions, urls_processed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                extraction_id,
                name,
                timestamp,
                input_method,
                len(urls),
                round(processing_time, 2),
                total_emails_found,
                successful_extractions,
                failed_extractions,
                json.dumps(urls)
            ))
            
            # Insert results
            for result in results:
                emails = result.get('emails', [])[:5] if result.get('emails') else []
                source_pages = result.get('email_sources', [])
                source_str = ', '.join(source_pages) if source_pages else ''
                
                cursor.execute("""
                    INSERT INTO extraction_results
                    (extraction_id, website_url, email_1, email_2, email_3, email_4, email_5,
                     source_pages, contact_form_found, status, pages_crawled)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    extraction_id,
                    result.get('url', ''),
                    emails[0] if len(emails) > 0 else None,
                    emails[1] if len(emails) > 1 else None,
                    emails[2] if len(emails) > 2 else None,
                    emails[3] if len(emails) > 3 else None,
                    emails[4] if len(emails) > 4 else None,
                    source_str,
                    result.get('has_contact_form', False),
                    result.get('status', ''),
                    result.get('successful_pages', 0)
                ))
            
            # Keep only latest 15 entries
            cursor.execute("""
                SELECT id FROM extractions 
                ORDER BY timestamp DESC 
                LIMIT 1000 OFFSET 15
            """)
            old_ids = [row[0] for row in cursor.fetchall()]
            
            if old_ids:
                placeholders = ','.join(['%s'] * len(old_ids))
                cursor.execute(f"DELETE FROM extractions WHERE id IN ({placeholders})", old_ids)
            
            conn.commit()
            logger.info(f"Saved extraction {extraction_id}")
            return extraction_id
            
        except Error as e:
            logger.error(f"Error saving extraction: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
    
    def load_history(self) -> List[Dict]:
        """
        Load all history entries
        
        Returns:
            List[Dict]: List of history entries
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM extractions 
                ORDER BY timestamp DESC 
                LIMIT 15
            """)
            extractions = cursor.fetchall()
            
            history = []
            for ext in extractions:
                # Get results for this extraction
                cursor.execute("""
                    SELECT * FROM extraction_results 
                    WHERE extraction_id = %s
                """, (ext['id'],))
                results_data = cursor.fetchall()
                
                # Convert results to expected format
                results = []
                for res in results_data:
                    emails = []
                    for i in range(1, 6):
                        email = res.get(f'email_{i}')
                        if email:
                            emails.append(email)
                    
                    results.append({
                        'url': res['website_url'],
                        'emails': emails,
                        'email_sources': res['source_pages'].split(', ') if res['source_pages'] else [],
                        'has_contact_form': bool(res['contact_form_found']),
                        'status': res['status'],
                        'successful_pages': res['pages_crawled']
                    })
                
                # Reconstruct URLs list
                urls_processed = json.loads(ext['urls_processed']) if ext['urls_processed'] else []
                
                # Handle timestamp conversion
                timestamp = ext['timestamp']
                if isinstance(timestamp, datetime):
                    timestamp_str = timestamp.isoformat()
                elif hasattr(timestamp, 'isoformat'):
                    timestamp_str = timestamp.isoformat()
                else:
                    timestamp_str = str(timestamp)
                
                history.append({
                    'id': ext['id'],
                    'name': ext['name'],
                    'timestamp': timestamp_str,
                    'input_method': ext['input_method'],
                    'urls_processed': urls_processed,
                    'total_urls': ext['total_urls'],
                    'processing_time': float(ext['processing_time']),
                    'results': results,
                    'total_emails_found': ext['total_emails_found'],
                    'successful_extractions': ext['successful_extractions'],
                    'failed_extractions': ext['failed_extractions']
                })
            
            return history
            
        except Error as e:
            logger.error(f"Error loading history: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def get_entry_by_id(self, entry_id: str) -> Optional[Dict]:
        """
        Get a specific history entry by ID
        
        Args:
            entry_id (str): ID of the entry to retrieve
        
        Returns:
            Optional[Dict]: History entry or None if not found
        """
        history = self.load_history()
        for entry in history:
            if entry.get('id') == entry_id:
                return entry
        return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a history entry by ID
        
        Args:
            entry_id (str): ID of the entry to delete
        
        Returns:
            bool: True if deleted, False if not found
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete will cascade to extraction_results due to foreign key
            cursor.execute("DELETE FROM extractions WHERE id = %s", (entry_id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            return deleted
            
        except Error as e:
            logger.error(f"Error deleting entry: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def delete_all_history(self) -> bool:
        """
        Delete all history entries
        
        Returns:
            bool: True if successful
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM extractions")
            conn.commit()
            return True
            
        except Error as e:
            logger.error(f"Error deleting all history: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def search_history(self, query: str) -> List[Dict]:
        """
        Search history by URL or email
        
        Args:
            query (str): Search query
        
        Returns:
            List[Dict]: Matching history entries
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query_pattern = f"%{query}%"
            
            # Search in extractions (URLs) and extraction_results (emails)
            cursor.execute("""
                SELECT DISTINCT e.id FROM extractions e
                LEFT JOIN extraction_results er ON e.id = er.extraction_id
                WHERE e.urls_processed LIKE %s 
                   OR er.website_url LIKE %s
                   OR er.email_1 LIKE %s
                   OR er.email_2 LIKE %s
                   OR er.email_3 LIKE %s
                   OR er.email_4 LIKE %s
                   OR er.email_5 LIKE %s
                ORDER BY e.timestamp DESC
                LIMIT 15
            """, (query_pattern, query_pattern, query_pattern, query_pattern, 
                  query_pattern, query_pattern, query_pattern))
            
            extraction_ids = [row[0] for row in cursor.fetchall()]
            
            # Load full history for matching IDs
            all_history = self.load_history()
            matching_entries = [entry for entry in all_history if entry['id'] in extraction_ids]
            
            return matching_entries
            
        except Error as e:
            logger.error(f"Error searching history: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def get_statistics(self) -> Dict:
        """
        Get overall statistics from history
        
        Returns:
            Dict: Statistics dictionary
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_extractions,
                    SUM(total_urls) as total_urls_processed,
                    SUM(total_emails_found) as total_emails_found,
                    AVG(processing_time) as average_processing_time,
                    SUM(successful_extractions) as total_successful,
                    SUM(failed_extractions) as total_failed
                FROM extractions
            """)
            
            result = cursor.fetchone()
            
            if result and result[0]:
                return {
                    'total_extractions': result[0] or 0,
                    'total_urls_processed': result[1] or 0,
                    'total_emails_found': result[2] or 0,
                    'average_processing_time': round(float(result[3] or 0), 2),
                    'total_successful': result[4] or 0,
                    'total_failed': result[5] or 0
                }
            else:
                return {
                    'total_extractions': 0,
                    'total_urls_processed': 0,
                    'total_emails_found': 0,
                    'average_processing_time': 0,
                    'total_successful': 0,
                    'total_failed': 0
                }
                
        except Error as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'total_extractions': 0,
                'total_urls_processed': 0,
                'total_emails_found': 0,
                'average_processing_time': 0,
                'total_successful': 0,
                'total_failed': 0
            }
        finally:
            if cursor:
                cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
