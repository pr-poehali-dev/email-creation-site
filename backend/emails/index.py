'''
Business: Handle email operations - instant internal mail system
Args: event with httpMethod, body (recipient, subject, body, is_draft), headers (X-User-Id)
Returns: HTTP response with email data or list of emails
'''

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import psycopg2
import psycopg2.extras
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id, X-Auth-Token',
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
    
    db_url = os.environ.get('DATABASE_URL')
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        if method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            box = query_params.get('box', 'inbox')
            
            cur.execute("SELECT email FROM users WHERE id = %s", (int(user_id),))
            user_result = cur.fetchone()
            
            if not user_result:
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
            
            if box == 'inbox':
                # Get all emails for user's primary email and additional emails
                cur.execute(
                    """
                    SELECT e.id, u.email as sender_email, e.subject, e.body, e.is_read, e.sent_at
                    FROM emails e
                    JOIN users u ON e.sender_id = u.id
                    WHERE (e.recipient_email = %s 
                           OR e.recipient_email IN (SELECT email FROM user_emails WHERE user_id = %s))
                          AND e.is_draft = FALSE
                    ORDER BY e.sent_at DESC
                    """,
                    (user_email, int(user_id))
                )
            elif box == 'sent':
                cur.execute(
                    """
                    SELECT id, recipient_email, subject, body, is_read, sent_at
                    FROM emails
                    WHERE sender_id = %s AND is_draft = FALSE
                    ORDER BY sent_at DESC
                    """,
                    (int(user_id),)
                )
            elif box == 'drafts':
                cur.execute(
                    """
                    SELECT id, recipient_email, subject, body, is_read, created_at
                    FROM emails
                    WHERE sender_id = %s AND is_draft = TRUE
                    ORDER BY created_at DESC
                    """,
                    (int(user_id),)
                )
            else:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Invalid box parameter'}),
                    'isBase64Encoded': False
                }
            
            emails = []
            for row in cur.fetchall():
                email_data = {
                    'id': row[0],
                    'from' if box == 'inbox' else 'to': row[1],
                    'subject': row[2],
                    'body': row[3],
                    'is_read': row[4],
                    'sent_at': row[5].isoformat() if row[5] else None
                }
                emails.append(email_data)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'emails': emails}),
                'isBase64Encoded': False
            }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            action = body_data.get('action', 'send')
            
            if action == 'send' or action == 'draft':
                recipient_email = body_data.get('recipient_email', '').strip()
                subject = body_data.get('subject', '').strip()
                body_text = body_data.get('body', '').strip()
                is_draft = action == 'draft'
                
                if not recipient_email or not subject or not body_text:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'recipient_email, subject, and body are required'}),
                        'isBase64Encoded': False
                    }
                
                # Check if recipient exists, if not - create external user
                cur.execute("SELECT id FROM users WHERE email = %s", (recipient_email,))
                recipient_result = cur.fetchone()
                
                if not recipient_result:
                    # Create external user automatically
                    username = recipient_email.split('@')[0]
                    cur.execute(
                        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                        (username, recipient_email, 'external_user')
                    )
                    cur.execute("SELECT id FROM users WHERE email = %s", (recipient_email,))
                    recipient_result = cur.fetchone()
                
                # Save to database
                cur.execute(
                    """
                    INSERT INTO emails (sender_id, recipient_email, subject, body, is_draft)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (int(user_id), recipient_email, subject, body_text, is_draft)
                )
                email_id = cur.fetchone()[0]
                
                # Send via SMTP if not draft
                if not is_draft:
                    smtp_host = os.environ.get('SMTP_HOST')
                    smtp_port = int(os.environ.get('SMTP_PORT', 465))
                    smtp_user = os.environ.get('SMTP_USER')
                    smtp_password = os.environ.get('SMTP_PASSWORD')
                    
                    msg = MIMEMultipart()
                    msg['From'] = smtp_user
                    msg['To'] = recipient_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body_text, 'plain'))
                    
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port)
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    server.quit()
                
                return {
                    'statusCode': 201,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'email_id': email_id,
                        'message': 'Draft saved' if is_draft else 'Email sent via SMTP'
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'mark_read':
                email_id = body_data.get('email_id')
                
                if not email_id:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'email_id is required'}),
                        'isBase64Encoded': False
                    }
                
                cur.execute(
                    "UPDATE emails SET is_read = TRUE WHERE id = %s",
                    (email_id,)
                )
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': True}),
                    'isBase64Encoded': False
                }
            
            elif action == 'check_inbox':
                imap_host = os.environ.get('IMAP_HOST')
                imap_port = int(os.environ.get('IMAP_PORT', 993))
                imap_user = os.environ.get('IMAP_USER')
                imap_password = os.environ.get('IMAP_PASSWORD')
                
                mail = imaplib.IMAP4_SSL(imap_host, imap_port)
                mail.login(imap_user, imap_password)
                mail.select('INBOX')
                
                status, messages = mail.search(None, 'UNSEEN')
                email_ids = messages[0].split()
                
                new_emails = []
                for email_id in email_ids[-10:]:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = msg['subject']
                    sender = msg['from']
                    body = ''
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    cur.execute("SELECT id FROM users WHERE email = %s", (imap_user,))
                    receiver = cur.fetchone()
                    receiver_id = receiver[0] if receiver else None
                    
                    if receiver_id:
                        cur.execute(
                            """
                            INSERT INTO emails (sender_id, recipient_email, subject, body, is_draft, is_read)
                            VALUES (%s, %s, %s, %s, FALSE, FALSE)
                            """,
                            (1, imap_user, subject or '(no subject)', body[:1000], )
                        )
                    
                    new_emails.append({
                        'from': sender,
                        'subject': subject,
                        'body': body[:200]
                    })
                
                mail.logout()
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'new_emails': len(new_emails),
                        'emails': new_emails
                    }),
                    'isBase64Encoded': False
                }
            
            else:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Invalid action'}),
                    'isBase64Encoded': False
                }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'}),
                'isBase64Encoded': False
            }
    finally:
        cur.close()
        conn.close()