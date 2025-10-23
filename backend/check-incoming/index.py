'''
Business: Check IMAP inbox and import new emails to database
Args: event with httpMethod, headers (X-User-Id)
Returns: HTTP response with count of imported emails
'''

import json
import os
import imaplib
import email
from email.header import decode_header
from typing import Dict, Any, List
from datetime import datetime
import psycopg2

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    headers = event.get('headers', {})
    user_id = headers.get('x-user-id') or headers.get('X-User-Id')
    
    if not user_id:
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Unauthorized. X-User-Id header required'}),
            'isBase64Encoded': False
        }
    
    imap_host = os.environ.get('IMAP_HOST')
    imap_port = int(os.environ.get('IMAP_PORT', '993'))
    imap_user = os.environ.get('IMAP_USER')
    imap_password = os.environ.get('IMAP_PASSWORD')
    
    if not all([imap_host, imap_user, imap_password]):
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'IMAP credentials not configured'}),
            'isBase64Encoded': False
        }
    
    db_url = os.environ.get('DATABASE_URL')
    
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(imap_user, imap_password)
        mail.select('INBOX')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        
        imported_count = 0
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get user email
        cur.execute("SELECT email FROM users WHERE id = %s", (int(user_id),))
        user_result = cur.fetchone()
        
        if not user_result:
            mail.logout()
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'User not found'}),
                'isBase64Encoded': False
            }
        
        user_email = user_result[0]
        
        for email_id in email_ids[-10:]:  # Process last 10 unread emails
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode subject
                    subject_raw = msg['Subject']
                    if subject_raw:
                        decoded_subject = decode_header(subject_raw)[0]
                        subject = decoded_subject[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(decoded_subject[1] or 'utf-8')
                    else:
                        subject = '(No Subject)'
                    
                    # Get sender
                    from_email = msg['From']
                    
                    # Get body
                    body = ''
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    # Check if email is for this user
                    to_email = msg['To']
                    if user_email.lower() in to_email.lower():
                        # Find or create sender
                        cur.execute("SELECT id FROM users WHERE email = %s", (from_email,))
                        sender_result = cur.fetchone()
                        
                        if sender_result:
                            sender_id = sender_result[0]
                        else:
                            # Create external sender
                            cur.execute(
                                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                                (from_email.split('@')[0], from_email, 'external')
                            )
                            sender_id = cur.fetchone()[0]
                        
                        # Insert email
                        cur.execute(
                            """
                            INSERT INTO emails (sender_id, recipient_email, subject, body, is_draft, is_read)
                            VALUES (%s, %s, %s, %s, FALSE, FALSE)
                            """,
                            (sender_id, user_email, subject, body)
                        )
                        imported_count += 1
        
        mail.logout()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'imported': imported_count,
                'message': f'Imported {imported_count} new emails'
            }),
            'isBase64Encoded': False
        }
    
    except imaplib.IMAP4.error as imap_error:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'IMAP error: {str(imap_error)}'
            }),
            'isBase64Encoded': False
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Server error: {str(e)}'
            }),
            'isBase64Encoded': False
        }
