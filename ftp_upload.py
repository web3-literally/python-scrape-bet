import shutil
from datetime import datetime

from ftplib import FTP
from zipfile import ZipFile

ftp = FTP("185.201.145.121")
ftp.login("daparto_scrap", "nNKRfeP4ZpIs")
path = '/output_data/'
ftp.cwd(path)
now = datetime.now().strftime("%Y_%m_%d")
filename = f"daparto_result_{now}.zip"
with ZipFile(filename, 'w') as zipObj:
    zipObj.write('dapartocomp.csv')
    zipObj.write('dapartoitem.csv')


with open(filename, 'rb') as f:
    ftp.storbinary('STOR %s' % filename, f) 

now = datetime.now().strftime("%Y%m%d%H%M%S")
now = datetime.now().strftime("%Y_%m_%d")
filename = f"daparto_result_{now}.zip"
shutil.copy("daparto_result.zip", f"output_history/{filename}")