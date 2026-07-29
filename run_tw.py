"""
在寄送 Email 前，把簡體內容自動轉換成繁體中文。
只影響 SMTP 實際送出的郵件內容，不影響其他推播管道（Telegram/飞书等）。
"""
import smtplib
import email
import opencc

converter = opencc.OpenCC('s2t')  # 簡體轉繁體

_original_sendmail = smtplib.SMTP.sendmail


def _convert_msg(raw_msg):
    try:
        if isinstance(raw_msg, bytes):
            msg_obj = email.message_from_bytes(raw_msg)
        else:
            msg_obj = email.message_from_string(raw_msg)

        for part in msg_obj.walk():
            if part.get_content_maintype() == 'text':
                charset = part.get_content_charset() or 'utf-8'
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode(charset, errors='ignore')
                    converted = converter.convert(text)
                    part.set_payload(converted, charset=charset)

        result = msg_obj.as_string()
        return result if isinstance(raw_msg, str) else result.encode('utf-8')
    except Exception as e:
        print(f"[繁體轉換] 轉換失敗，改用原始內容: {e}")
        return raw_msg


def patched_sendmail(self, from_addr, to_addrs, msg, *args, **kwargs):
    msg = _convert_msg(msg)
    return _original_sendmail(self, from_addr, to_addrs, msg, *args, **kwargs)


smtplib.SMTP.sendmail = patched_sendmail
smtplib.SMTP_SSL.sendmail = patched_sendmail

# 套用轉換後，照原本方式啟動主程式
import runpy
runpy.run_path('main.py', run_name='__main__')
