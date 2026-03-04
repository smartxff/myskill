#!/usr/bin/env python3
import argparse
import json
import sys
import email
from pathlib import Path
from datetime import datetime

import imaplib
import email

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "configs" / "email-reader.json"
HISTORY_FILE = Path(__file__).resolve().parent.parent.parent / "configs" / "email-reader-history.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"email": "", "password": ""}

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"read_ids": []}

def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def connect_mail(config):
    try:
        mail = imaplib.IMAP4_SSL('imap.qq.com')
        mail.login(config['email'], config['password'])
        return mail
    except Exception as e:
        print(f"Error: Failed to connect - {str(e)}", file=sys.stderr)
        sys.exit(1)

def get_emails(limit=10, unread_only=False):
    config = load_config()
    if not config['email'] or not config['password']:
        print("Error: Please configure email and password in configs/email-reader.json")
        sys.exit(1)
    
    mail = connect_mail(config)
    mail.select('INBOX')
    
    search_criteria = 'ALL'
    if unread_only:
        search_criteria = 'UNSEEN'
    
    typ, messages = mail.search(None, search_criteria)
    email_ids = messages[0].split()[-limit:] if limit else messages[0].split()
    
    results = []
    history = load_history()
    
    for eid in email_ids:
        typ, msg_data = mail.fetch(eid, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg_content = response_part[1]
                msg = email.message_from_bytes(msg_content)
                
                subject = email.header.decode_header(msg['Subject'])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode('utf-8')
                
                from_addr = email.header.decode_header(msg['From'])[0][0]
                if isinstance(from_addr, bytes):
                    from_addr = from_addr.decode('utf-8')
                
                date = msg['Date']
                message_id = msg['Message-ID']
                
                results.append({
                    "email_id": eid.decode() if isinstance(eid, bytes) else eid,
                    "message_id": message_id,
                    "from": from_addr,
                    "subject": subject,
                    "date": date,
                    "unread": 'SEEN' not in str(msg_data)
                })
                
                if message_id not in history['read_ids']:
                    history['read_ids'].append(message_id)
    
    save_history(history)
    mail.logout()
    return results

def get_email_detail(email_id=None, message_id=None):
    config = load_config()
    if not config['email'] or not config['password']:
        print("Error: Please configure email and password in configs/email-reader.json")
        sys.exit(1)
    
    mail = connect_mail(config)
    mail.select('INBOX')
    
    if email_id:
        typ, msg_data = mail.fetch(email_id, '(RFC822)')
    elif message_id:
        clean_id = message_id.strip().strip('<').strip('>')
        typ, messages = mail.search(None, 'ALL')
        all_ids = messages[0].split()
        
        found_eid = None
        for eid in all_ids:
            typ, msg_data = mail.fetch(eid, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg_content = response_part[1]
                    msg = email.message_from_bytes(msg_content)
                    msg_id = msg.get('Message-ID', '')
                    if clean_id in msg_id:
                        found_eid = eid
                        break
            if found_eid:
                break
        
        if not found_eid:
            print(f"Error: Email not found for message-id: {message_id}")
            sys.exit(1)
        
        typ, msg_data = mail.fetch(found_eid, '(RFC822)')
    else:
        print("Error: --email-id or --message-id is required")
        sys.exit(1)
    
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg_content = response_part[1]
            msg = email.message_from_bytes(msg_content)
            
            subject = email.header.decode_header(msg['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode('utf-8')
            
            from_addr = email.header.decode_header(msg['From'])[0][0]
            if isinstance(from_addr, bytes):
                from_addr = from_addr.decode('utf-8')
            
            to_addr = msg['To'] or ""
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/html':
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                        except:
                            body = part.get_payload(decode=True).decode('gbk', errors='ignore')
                        break
                    elif content_type == 'text/plain' and not body:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                        except:
                            body = part.get_payload(decode=True).decode('gbk', errors='ignore')
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8')
                except:
                    body = msg.get_payload(decode=True).decode('gbk', errors='ignore')
            
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        attachments.append(part.get_filename())
            
            result = {
                "message_id": msg['Message-ID'],
                "from": from_addr,
                "to": to_addr,
                "subject": subject,
                "date": msg['Date'],
                "body": body,
                "attachments": attachments
            }
            
            history = load_history()
            if msg['Message-ID'] not in history['read_ids']:
                history['read_ids'].append(msg['Message-ID'])
                save_history(history)
            
            mail.logout()
            return result
    
    mail.logout()
    return None

def main():
    parser = argparse.ArgumentParser(description="Email Reader - QQ邮箱邮件读取")
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    list_parser = subparsers.add_parser('list', help='获取邮件列表')
    list_parser.add_argument('--limit', type=int, default=10, help='获取数量')
    list_parser.add_argument('--unread', action='store_true', help='只显示未读')
    list_parser.add_argument('--output', help='输出文件')
    
    read_parser = subparsers.add_parser('read', help='读取邮件详情')
    read_parser.add_argument('--email-id', help='邮件序号(从list获取)')
    read_parser.add_argument('--message-id', help='邮件Message-ID')
    read_parser.add_argument('--output', help='输出文件')
    
    config_parser = subparsers.add_parser('config', help='配置')
    config_parser.add_argument('--email', help='QQ邮箱')
    config_parser.add_argument('--password', help='授权码')
    
    args = parser.parse_args()
    
    if args.command == 'config':
        config = load_config()
        if args.email:
            config['email'] = args.email
        if args.password:
            config['password'] = args.password
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Config saved to {CONFIG_FILE}")
        return
    
    if args.command == 'list':
        results = get_emails(args.limit, args.unread)
        output = json.dumps(results, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"List saved to {args.output}")
        else:
            print(output)
    
    if args.command == 'read':
        result = get_email_detail(args.email_id, args.message_id)
        if result:
            output = json.dumps(result, ensure_ascii=False, indent=2)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
                print(f"Email saved to {args.output}")
            else:
                print(output)
        else:
            print("Email not found")

if __name__ == "__main__":
    main()
