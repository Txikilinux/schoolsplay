#! /usr/bin/python
# -*- coding: utf-8 -*-

#create logger, logger was configured in SPLoggin
import logging
module_logger = logging.getLogger("schoolsplay.Mail")

import smtplib
from time import strftime
from email import encoders
from email.MIMEMultipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.MIMEText import MIMEText
import zipfile
import os
import tempfile
import utils
BODY = \
"""
Milestone: %(milestone)s
Component: %(component)s
Priority: %(prio)s
Assigned-to: %(assigned)s
Description: %(description)s

Additional info: 
Reported by: %(name)s mac: %(mac)s ip: %(ip)s date: %(date)s
.
"""

class SendmailError(Exception):
    pass
    
def mail(subject='', description='', component='', prio='', assigned='', \
         milestone='', name='', imgpath='', logpath=''):
    data = {'subject':subject, 'description':description, 'component':component, \
            'prio':prio, 'assigned':assigned, 'milestone':milestone, \
            'imgpath':imgpath, 'date':utils.current_time(), \
            'mac': get_mac(), 'ip': get_ip(), 'name':name}
    #Sender
    gmail_user = "splogfiles@gmail.com"# pass is spam2010
    #Recipient 
    gmail_to = "braintrainer@tickets.assembla.com"
    #Sender pass
    gmail_pwd = "spam2010"
    if logpath:
        zf = tempfile.TemporaryFile(prefix='splog', suffix='.zip')
        zip = zipfile.ZipFile(zf, 'w')
        zip.write(logpath)
        zip.close()
        zf.seek(0)
    
    mailServer = None
    module_logger.debug("Starting to mail logfile")
    
    body = BODY % data
    
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_to
    msg["Subject"] = data['subject']
    msg.attach(MIMEText(body))

    if logpath:
        zip = MIMEBase('application', 'zip')
        zip.set_payload(zf.read())
        encoders.encode_base64(zip)
        zip.add_header('Content-Disposition', 'attachment', filename= logpath + '.zip')
        msg.attach(zip)

    if imgpath:
        img = MIMEImage(open(data['imgpath'],'rb').read())
        img.add_header('Content-Disposition', 'attachment', filename=data['imgpath'])
        msg.attach(img)
    try:
        mailServer = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(gmail_user, gmail_pwd)
        mailServer.sendmail(gmail_user, gmail_to, msg.as_string())
    except Exception, msg:
        module_logger.debug("Failed to send mail, please report this.%s" % msg)
        raise SendmailError,msg
    else:
        mailServer.close()
        module_logger.debug("Mail send to: %s" % str(gmail_to))
    finally:
        if mailServer:
            mailServer.close()

def get_mac():
    for line in os.popen("/sbin/ifconfig"):
        if line.find('Ether') and line.find('eth') > -1:
            mac = line.split()[4]
            break
        else:
            mac = 'No mac found'
    return mac
    
def get_ip():
    for line in os.popen("/sbin/ifconfig"):
        if line.find('inet addr:') and line.find('Bcast:')> -1:
            ip = line.split()[1][5:]
            break
        else:
            ip = 'No ip found'
    return ip

if __name__ == '__main__':
    # Beware that this will create a new logfile so the file mailed will be this logfile
    import SPLogging
    SPLogging.set_level('debug')
    SPLogging.start()

    img = os.path.join(os.getcwd(),'test.jpg')
    
    #mail(subject='', description='', component='', prio='', assigned='', \
    #    milestone='', imgpath=''):
    mail(subject='test_1 ticket from new mail script', description='description of the problem text', \
         component='core', prio='2' , assigned='stas zytkiewicz', milestone='BT2.1', \
         imgpath=img)
