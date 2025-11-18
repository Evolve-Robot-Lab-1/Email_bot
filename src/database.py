"""
Database module for campaign analytics and tracking
SQLite database for persistent storage of campaign data
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class CampaignDatabase:
    """Manages campaign analytics database"""

    def __init__(self, db_path='campaign_analytics.db'):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                goal TEXT,
                subject_template TEXT,
                message_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'draft',
                total_recipients INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                opened_count INTEGER DEFAULT 0,
                clicked_count INTEGER DEFAULT 0,
                replied_count INTEGER DEFAULT 0,
                bounced_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')

        # Recipients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                email TEXT NOT NULL,
                company_name TEXT,
                industry TEXT,
                company_size TEXT,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                replied_at TIMESTAMP,
                bounced_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        ''')

        # Email events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id INTEGER,
                event_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (recipient_id) REFERENCES recipients(id)
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaigns(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipient_campaign ON recipients(campaign_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipient_email ON recipients(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_recipient ON email_events(recipient_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON email_events(event_type)')

        conn.commit()
        conn.close()

    def create_campaign(self, campaign_data: Dict) -> str:
        """Create a new campaign"""
        conn = self.get_connection()
        cursor = conn.cursor()

        campaign_id = campaign_data.get('id', f"campaign_{datetime.now().strftime('%Y%m%d%H%M%S')}")

        cursor.execute('''
            INSERT INTO campaigns
            (id, name, goal, subject_template, message_template, status, total_recipients, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign_id,
            campaign_data.get('name', 'Untitled Campaign'),
            campaign_data.get('goal', ''),
            campaign_data.get('subject_template', ''),
            campaign_data.get('message_template', ''),
            campaign_data.get('status', 'draft'),
            campaign_data.get('total_recipients', 0),
            json.dumps(campaign_data.get('metadata', {}))
        ))

        conn.commit()
        conn.close()
        return campaign_id

    def add_recipients(self, campaign_id: str, recipients: List[Dict]):
        """Add recipients to a campaign"""
        conn = self.get_connection()
        cursor = conn.cursor()

        for recipient in recipients:
            cursor.execute('''
                INSERT INTO recipients
                (campaign_id, email, company_name, industry, company_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                campaign_id,
                recipient.get('email', ''),
                recipient.get('Company_Name', recipient.get('company', '')),
                recipient.get('Industry', ''),
                recipient.get('Company_Size', '')
            ))

        # Update total recipients count
        cursor.execute('''
            UPDATE campaigns
            SET total_recipients = (SELECT COUNT(*) FROM recipients WHERE campaign_id = ?)
            WHERE id = ?
        ''', (campaign_id, campaign_id))

        conn.commit()
        conn.close()

    def update_email_status(self, campaign_id: str, email: str, status: str, timestamp: datetime = None):
        """Update email send status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        timestamp = timestamp or datetime.now()

        # Update recipient status
        status_field = f"{status}_at"
        cursor.execute(f'''
            UPDATE recipients
            SET status = ?, {status_field} = ?
            WHERE campaign_id = ? AND email = ?
        ''', (status, timestamp, campaign_id, email))

        # Update campaign counts
        if status == 'sent':
            cursor.execute('UPDATE campaigns SET sent_count = sent_count + 1 WHERE id = ?', (campaign_id,))
        elif status == 'opened':
            cursor.execute('UPDATE campaigns SET opened_count = opened_count + 1 WHERE id = ?', (campaign_id,))
        elif status == 'clicked':
            cursor.execute('UPDATE campaigns SET clicked_count = clicked_count + 1 WHERE id = ?', (campaign_id,))
        elif status == 'replied':
            cursor.execute('UPDATE campaigns SET replied_count = replied_count + 1 WHERE id = ?', (campaign_id,))
        elif status == 'bounced':
            cursor.execute('UPDATE campaigns SET bounced_count = bounced_count + 1 WHERE id = ?', (campaign_id,))

        # Add event
        recipient_id = cursor.execute(
            'SELECT id FROM recipients WHERE campaign_id = ? AND email = ?',
            (campaign_id, email)
        ).fetchone()

        if recipient_id:
            cursor.execute('''
                INSERT INTO email_events (recipient_id, event_type, timestamp)
                VALUES (?, ?, ?)
            ''', (recipient_id[0], status, timestamp))

        conn.commit()
        conn.close()

    def get_campaign_stats(self, campaign_id: str = None) -> Dict:
        """Get campaign statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if campaign_id:
            # Get specific campaign stats
            result = cursor.execute('''
                SELECT
                    id, name, goal, status,
                    total_recipients, sent_count, opened_count,
                    clicked_count, replied_count, bounced_count,
                    created_at
                FROM campaigns
                WHERE id = ?
            ''', (campaign_id,)).fetchone()

            if result:
                stats = {
                    'id': result[0],
                    'name': result[1],
                    'goal': result[2],
                    'status': result[3],
                    'total_recipients': result[4],
                    'sent': result[5],
                    'opened': result[6],
                    'clicked': result[7],
                    'replied': result[8],
                    'bounced': result[9],
                    'created_at': result[10],
                    'open_rate': (result[6] / result[5] * 100) if result[5] > 0 else 0,
                    'click_rate': (result[7] / result[5] * 100) if result[5] > 0 else 0,
                    'reply_rate': (result[8] / result[5] * 100) if result[5] > 0 else 0
                }
            else:
                stats = {}
        else:
            # Get overall stats
            result = cursor.execute('''
                SELECT
                    COUNT(*) as total_campaigns,
                    SUM(sent_count) as total_sent,
                    SUM(opened_count) as total_opened,
                    SUM(clicked_count) as total_clicked,
                    SUM(replied_count) as total_replied,
                    SUM(bounced_count) as total_bounced
                FROM campaigns
            ''').fetchone()

            stats = {
                'total_campaigns': result[0] or 0,
                'total_sent': result[1] or 0,
                'total_opened': result[2] or 0,
                'total_clicked': result[3] or 0,
                'total_replied': result[4] or 0,
                'total_bounced': result[5] or 0,
                'overall_open_rate': (result[2] / result[1] * 100) if result[1] else 0,
                'overall_click_rate': (result[3] / result[1] * 100) if result[1] else 0,
                'overall_reply_rate': (result[4] / result[1] * 100) if result[1] else 0
            }

        conn.close()
        return stats

    def get_all_campaigns(self) -> List[Dict]:
        """Get all campaigns with stats"""
        conn = self.get_connection()
        cursor = conn.cursor()

        results = cursor.execute('''
            SELECT
                id, name, goal, status,
                total_recipients, sent_count, opened_count,
                clicked_count, replied_count, bounced_count,
                created_at
            FROM campaigns
            ORDER BY created_at DESC
        ''').fetchall()

        campaigns = []
        for row in results:
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'goal': row[2],
                'status': row[3],
                'total_recipients': row[4],
                'sent': row[5],
                'opened': row[6],
                'clicked': row[7],
                'replied': row[8],
                'bounced': row[9],
                'created_at': row[10],
                'open_rate': (row[6] / row[5] * 100) if row[5] > 0 else 0,
                'click_rate': (row[7] / row[5] * 100) if row[5] > 0 else 0,
                'reply_rate': (row[8] / row[5] * 100) if row[5] > 0 else 0
            })

        conn.close()
        return campaigns

    def get_recipient_details(self, campaign_id: str) -> List[Dict]:
        """Get detailed recipient information for a campaign"""
        conn = self.get_connection()
        cursor = conn.cursor()

        results = cursor.execute('''
            SELECT
                email, company_name, industry, status,
                sent_at, opened_at, clicked_at, replied_at, bounced_at
            FROM recipients
            WHERE campaign_id = ?
            ORDER BY sent_at DESC
        ''', (campaign_id,)).fetchall()

        recipients = []
        for row in results:
            recipients.append({
                'email': row[0],
                'company': row[1],
                'industry': row[2],
                'status': row[3],
                'sent_at': row[4],
                'opened_at': row[5],
                'clicked_at': row[6],
                'replied_at': row[7],
                'bounced_at': row[8]
            })

        conn.close()
        return recipients

    def get_hourly_stats(self, campaign_id: str = None) -> List[Dict]:
        """Get hourly email statistics for charts"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                event_type,
                COUNT(*) as count
            FROM email_events
        '''

        if campaign_id:
            query += '''
                JOIN recipients ON email_events.recipient_id = recipients.id
                WHERE recipients.campaign_id = ?
            '''
            params = (campaign_id,)
        else:
            params = ()

        query += '''
            GROUP BY hour, event_type
            ORDER BY hour DESC
            LIMIT 168
        '''

        results = cursor.execute(query, params).fetchall()

        hourly_stats = []
        for row in results:
            hourly_stats.append({
                'hour': row[0],
                'event_type': row[1],
                'count': row[2]
            })

        conn.close()
        return hourly_stats

    def export_campaign_data(self, campaign_id: str) -> Dict:
        """Export all campaign data for download"""
        stats = self.get_campaign_stats(campaign_id)
        recipients = self.get_recipient_details(campaign_id)
        hourly = self.get_hourly_stats(campaign_id)

        return {
            'campaign': stats,
            'recipients': recipients,
            'hourly_stats': hourly
        }


# Singleton instance
_db = None

def get_db() -> CampaignDatabase:
    """Get or create database instance"""
    global _db
    if _db is None:
        _db = CampaignDatabase()
    return _db