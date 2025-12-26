import os
from datetime import datetime
import configparser
import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def return_current_outfolder(download_path,user_id,source_id):
    date_prefix = datetime.today().strftime("%Y-%m-%d")
    new_date=datetime.today().strftime("%Y%m%d")
    time_prefix = datetime.today().strftime("%H%M%S")
    out_path = os.path.join(download_path,date_prefix, user_id,f"{source_id}-IA_{new_date}_{time_prefix}")
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    return out_path

def return_temp_outfolder(download_path,user_id,source_id):
    date_prefix = datetime.today().strftime("%Y-%m-%d")
    out_path = os.path.join(download_path,date_prefix, user_id,f"{source_id}")
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    return out_path

def output_excel_name(current_path):
    return os.path.join(current_path,os.path.basename(current_path)+'.xlsx')

def output_TOC_name(current_path):
    return str(os.path.basename(current_path)+'.pdf')

def get_ini_file_values(path):
    config = configparser.ConfigParser()
    config.read(path)

    Download_Path = config.get('DETAILS', 'download path')
    Download_User = config.get('DETAILS', 'download user')
    Source_ID = config.get('DETAILS', 'source id')
    Email_Sent = config.get('DETAILS', 'email_sent')
    Check_duplicate = config.get('DETAILS', 'check_duplicate')
    Sending_address = config.get('DETAILS', 'sending address')
    Receiving_address = config.get('DETAILS', 'receiving address')
    CC = config.get('DETAILS', 'cc')
    Port = config.get('DETAILS', 'port')

    return (Download_Path,Download_User,Source_ID,Email_Sent,Check_duplicate,Sending_address,
            str(Receiving_address).split(","),str(CC).split(","),Port)

def read_ini_file(ini_path):
    Download_path, Download_user, Source_id, Email_sent, Check_duplicate,Sending_address, Receiving_address, CC, Port = get_ini_file_values(ini_path)
    if not os.path.exists(Download_path):
        os.makedirs(Download_path)
    return Download_path, Email_sent,Check_duplicate,Download_user

def attachment_for_email(url_id,duplicate_list,error_list,completed_list,pdf_count,ini_path,attachment,date_for_email,time_for_email,Ref_value):
    Download_path, Download_user, Source_id, Email_sent, Check_duplicate,Sending_address, Receiving_address, CC, Port = get_ini_file_values(ini_path)
    compose_email_to_send(url_id,duplicate_list,error_list,completed_list,pdf_count,attachment, date_for_email, time_for_email, Sending_address,Receiving_address, CC, Port,Ref_value)

def check_duplicate(doi,art_title,src_id,vol_no,iss_no):
    url = 'https://ism-portal.innodata.com/api/validate-record'

    data = {'token': '6547bdf3f07202413b5daf3216e511028c14034b36ff47c514c0220a911785b3:1698740839',
            'doi': doi, 'art_title': art_title, 'srcid': src_id, 'volume_no': vol_no, 'issue_no': iss_no}

    responseData = json.loads(BeautifulSoup(requests.post(url, data=data).content, 'html.parser').text)

    duplicateCheckValue=responseData.get("status",{})
    tpa_id=responseData.get("tpa_id",{})

    if not duplicateCheckValue:
        return True,tpa_id
    else:
        return False,tpa_id

def sendCountAsPost(url_id,Ref_value,Total_count,Downloaded_count,Duplicated_count,Error_count):
    url = "https://ism-portal.innodata.com/api/webcrawlers/add-info"

    headers = {
        "token": "6547bdf3f07202413b5daf3216e511028c14034b36ff47c514c0220a911785b3:1698740839",
        "Content-Type": "application/json"
    }

    payload = {
        'source_id': url_id,
        'ref_id': f'REF_{Ref_value}',
        'crawled_count': Total_count,
        'downloaded_count': Downloaded_count,
        'duplicate_count': Duplicated_count,
        'error_count': Error_count
    }

    response=requests.post(url,headers=headers,json=payload)

    if response.status_code == 200:
        print("✅ The download count POST request was sent successfully.")
    else:
        print(f"Failed to send POST request. Status code: {response.status_code}")

def email_body(email_date, email_time,skipped,errors,completed_list,download_count,source_id,Ref_value):
    subject = '{} downloaded details ({})'.format(source_id, email_date + ' ' + email_time)
    subject+=' Ref_'+ Ref_value
    body = ""

    if download_count == 0:
        string1 = "<p>Downloaded count: 0</p>"
    else:
        string1 = "<p>Downloaded count: {}</p>".format(download_count)

    if errors:
        errors_info = "<p><strong>Error links:</strong></p>\n<ul>\n{}</ul>".format(
            "\n".join("<li>{}</li>".format(item) for item in errors)
        )
        body += errors_info

    if skipped:
        skipped_info = "<p><strong>Skipped links:</strong></p>\n<ul>\n{}</ul>".format(
            "\n".join("<li>{}</li>".format(item) for item in skipped)
        )
        body += skipped_info

    if completed_list:
        completed_info = "<p><strong>Completed links:</strong></p>\n<ul>\n{}</ul>".format(
            "\n".join("<li>{}</li>".format(item) for item in completed_list)
        )
        body += completed_info

    body = "{}\n{}".format(string1, body)

    html_body = "<html><body>{}</body></html>".format(body)
    return subject,html_body

def send_email(subject, body, attachments,Sending_address,to_email_list,cc_email_list,port):
    if attachments is None:
        attachments = []
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    sender_address = Sending_address

    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = ", ".join(to_email_list)
    message['CC'] = ", ".join(cc_email_list)
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    if not attachments == []:
        csv_filename = attachments
        with open(attachments, "rb") as attachment:
            part = MIMEBase('multipart', 'plain')
            part.set_payload(attachment.read())
            attachment.close()
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {csv_filename}")
        message.attach(part)

    session = smtplib.SMTP('smtpsgp.innodata.com', port)
    text = message.as_string()
    session.sendmail(sender_address, to_email_list + cc_email_list, text)
    session.quit()
    print('✅ Mail Sent')

def compose_email_to_send(url_id,duplicate_list,error_list,completed_list,pdf_count,attachment, date_for_email, time_for_email,Sending_address,to_email_list,cc_email_list,port,Ref_value):
    subject,body = email_body(str(date_for_email), str(time_for_email),duplicate_list,error_list,completed_list,pdf_count,url_id,Ref_value)
    send_email(subject, body, attachment,Sending_address,to_email_list,cc_email_list,port)

def output_email_file(current_path):
    return os.path.join(current_path,'Email details.html')

def email_body_html(email_date, email_time,skipped,errors,completed_list,download_count,source_id,Ref_value,attachment,current_out):
    out_html_file = output_email_file(current_out)

    subject = '<h3>{}</h3>'.format('{} downloaded details ({}) Ref_{}'.format(source_id, email_date + ' ' + email_time, Ref_value))
    body = ""

    if download_count == 0:
        string1 = "<h4>Downloaded count: 0</h4>"
    else:
        string1 = "<h4>Downloaded count: {}</h4>".format(download_count)

    if errors:
        errors_info = "<h4><strong>Error links:</strong></h4>\n<ul>\n{}</ul>".format(
            "\n".join("<li>{}</li>".format(item) for item in errors)
        )
        body += errors_info

    if skipped:
        skipped_info = "<h4><strong>Skipped links:</strong></h4>\n<ul>\n{}</ul>".format(
            "\n".join("<li>{}</li>".format(item) for item in skipped)
        )
        body += skipped_info

    if completed_list:
        completed_info = "<h4><strong>Completed links:</strong></h4>\n<ul>\n{}</ul>".format(
            "\n".join("<li>{}</li>".format(item) for item in completed_list)
        )
        body += completed_info

    if attachment != None:
        file_link = f'<h4><a href="{attachment}">Excel file</a></h4>'
        body = "{}\n{}\n{}".format(file_link,string1, body)
    else:
        body = "{}\n{}".format( string1, body)

    html_body = "<html><body>{}</body></html>".format(body)
    content = subject+html_body

    with open(out_html_file, "w",encoding="utf-8") as file:
        file.write(content)
    print("✅ Email created!")









