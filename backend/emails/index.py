'''
Business: Handle email operations - send via SMTP, receive, list emails, drafts
Args: event with httpMethod, body (recipient, subject, body, is_draft), headers (X-User-Id)
Returns: HTTP response with email data or list of emails
'''

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
import psycopg2
import psycopg2.extras
from email_validator import validate_email, EmailNotValidError

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
                cur.execute(
                    """
                    SELECT e.id, u.email as sender_email, e.subject, e.body, e.is_read, e.sent_at
                    FROM emails e
                    JOIN users u ON e.sender_id = u.id
                    WHERE e.recipient_email = %s AND e.is_draft = FALSE
                    ORDER BY e.sent_at DESC
                    """,
                    (user_email,)
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
                
                # Validate email
                try:
                    validate_email(recipient_email, check_deliverability=False)
                except EmailNotValidError:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'Invalid email address'}),
                        'isBase64Encoded': False
                    }
                
                # Get sender email
                cur.execute("SELECT email FROM users WHERE id = %s", (int(user_id),))
                sender_result = cur.fetchone()
                if not sender_result:
                    return {
                        'statusCode': 404,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'User not found'}),
                        'isBase64Encoded': False
                    }
                sender_email = sender_result[0]
                
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
                    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
                    smtp_user = os.environ.get('SMTP_USER')
                    smtp_password = os.environ.get('SMTP_PASSWORD')
                    
                    if smtp_host and smtp_user and smtp_password:
                        try:
                            msg = MIMEMultipart('alternative')
                            msg['Subject'] = subject
                            msg['From'] = f"{sender_email} <{smtp_user}>"
                            msg['To'] = recipient_email
                            
                            text_part = MIMEText(body_text, 'plain', 'utf-8')
                            msg.attach(text_part)
                            
                            with smtplib.SMTP(smtp_host, smtp_port) as server:
                                server.starttls()
                                server.login(smtp_user, smtp_password)
                                server.send_message(msg)
                        except Exception as smtp_error:
                            # Log error but don't fail - email saved to DB
                            print(f"SMTP Error: {str(smtp_error)}")
                
                return {
                    'statusCode': 201,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'email_id': email_id,
                        'message': 'Draft saved' if is_draft else 'Email sent successfully'
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