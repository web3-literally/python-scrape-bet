from ftplib import FTP
from zipfile import ZipFile

ftp = FTP("185.201.145.121")
ftp.login("daparto_scrap", "nNKRfeP4ZpIs")
path = '/input_data/'
filename = 'input_items_for_scraping.zip'

ftp.cwd(path)
ftp.retrbinary("RETR " + filename ,open("/root/daparto/daparto/" + filename, 'wb').write)

with ZipFile("/root/daparto/daparto/" + filename, 'r') as zipObj:
    zipObj.extractall("/root/daparto/daparto/")