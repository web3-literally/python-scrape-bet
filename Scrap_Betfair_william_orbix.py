import os
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from PyQt5 import QtGui
from playsound import playsound
from bs4 import BeautifulSoup

import csv
import datetime
import json
import os
import requests
import sys
import threading
import time

threads = {}
eventDict = {}
eventWilliamHillDict = {}
oddCompareDuration = {}
gLock = threading.Lock()
scrapThread = None
williamHillThread = None


############################

class WilliamHillScraper():
    def __init__(self):
        self.current_url = ''
        self.isRunning = False
        self.browser = None
        self.main_url = 'http://sports.williamhill.it/bet_ita/it/betlive/24'

    def getCommonEventName(self, home, away):
        gLock.acquire()
        try:
            # print('eventDict Length: {0}', len(eventDict))
            for key, value in eventDict.items():
                include_home = False
                for sub_name in home.split():
                    if sub_name in value[0]:
                        include_home = True
                if include_home == False:
                    continue
                for sub_name in away.split():
                    if sub_name in value[0]:
                        gLock.release()
                        return key

            gLock.release()
            return ''
        except:
            print('getCommonEventName Except')
            gLock.release()
            return ''

    def scrapTennis(self):
        print('=== Starting tennis scrapping ===')

        while self.isRunning:
            try:
                inplay_block = self.browser.find_element_by_id('ip_sport_24')
                tbodies = inplay_block.find_elements_by_tag_name('tbody')
                for tbody in tbodies:
                    rows = tbody.find_elements_by_tag_name('tr')
                    for row in rows:
                        # get event name first
                        if row.value_of_css_property("display") == "none":
                            continue
                        event_name = row.find_element_by_class_name('CentrePad').find_element_by_tag_name('span').text
                        home_name = ''
                        away_name = ''
                        event_name_splits = event_name.split('₋')
                        if len(event_name_splits) < 2:
                            event_name_splits = event_name.split('-')

                        home_name = event_name_splits[0]
                        away_name = event_name_splits[1]

                        common_eventname = self.getCommonEventName(home_name, away_name)
                        if common_eventname == '':
                            continue

                        td_elements = row.find_elements_by_tag_name('td')

                        home_odds = td_elements[3].find_element_by_tag_name('div').find_element_by_tag_name('div').text
                        away_odds = td_elements[5].find_element_by_tag_name('div').find_element_by_tag_name('div').text

                        odds_values = [home_odds, away_odds]
                        eventWilliamHillDict[common_eventname] = odds_values

                sleep(0.01)
            except Exception as inst:
                # print('error ' + str(type(inst)) + ', '.join(str(x) for x in inst.args))
                continue

    def scrapping(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_path = os.path.join(os.path.dirname(__file__), 'drivers', 'chromedriver')
        print('===>>> chrome_path = ', chrome_path)
        chrome_options.add_argument("--incognito")
        # chrome_options.add_argument("--headless")
        self.browser = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)
        self.browser.get(self.main_url)
        self.current_url = self.main_url
        # sleep(3)
        # self.login()
        sleep(10)
        self.scrapTennis()

    def start_thread(self):
        print('williamHill_start_thread')
        self.isRunning = True
        williamHillThread = threading.Thread(target=self.scrapping)
        williamHillThread.start()
        print('williamHill_start_thread return')

    def stop_thread(self):
        self.isRunning = False
        sleep(2)

        try:
            williamHillThread.stop()
            del williamHillThread
            print('williamHill_Stopped')
        except:
            print('williamHill_Stop Failed')
            pass


class OrbixScraper():
    def __init__(self):
        self.current_url = ''
        self.isRunning = False
        self.browser = None
        self.main_url = 'https://orbitexch.com/customer/inplay'
        self.username = 'luca17'
        self.password = 'qq123qq'

    def login(self):
        self.browser.get('https://orbitexch.com/customer/login')
        while True:
            try:
                sleep(10)
                username_tag = self.browser.find_element_by_xpath('//input[@name="username"]')
                password_tag = self.browser.find_element_by_xpath('//input[@name="password"]')
                self.browser.execute_script("arguments[0].setAttribute('value','" + self.username + "')", username_tag)
                self.browser.execute_script("arguments[0].setAttribute('value','" + self.password + "')", password_tag)
                # username_tag.send_keys(self.username)
                # password_tag.send_keys(self.password)
                login_btn = self.browser.find_element_by_xpath('//input[@name="submit"]')
                login_btn.submit()
                break
            except Exception as e:
                print(e)
                continue

    def hasDisabledClass(self, element):
        return 'disabled' in element.get_attribute('class')

    def scrapTennis(self):
        print('=== Starting tennis scrapping ===')
        self.browser.get(self.main_url)
        self.current_url = self.main_url
        sleep(10)
        tennis_btn = self.browser.find_element_by_xpath('//li[@class="biab_inplay-tabs-item" and text()="Tennis"]')
        self.browser.execute_script("arguments[0].click();", tennis_btn)
        sleep(7)
        while self.isRunning:
            try:
                soup = BeautifulSoup(self.browser.page_source, 'html.parser')
                rows = soup.findAll('div', {'class': 'biab_table-wrapper'})
                for row in rows:
                    # get event name first
                    event_status = row.findAll('div', {'class': 'biab_market-title-team-names'})[0].text
                    event_name = event_status
                    odd_items = row.findAll('td', {'class': 'biab_green-cell'})
                    odd1 = odd_items[0].findAll('span', {'class': 'biab_odds'})[0].text
                    odd2 = odd_items[1].findAll('span', {'class': 'biab_odds'})[0].text
                    order_values = []
                    order_values.append(event_status)
                    order_values.append(odd1)
                    order_values.append(odd2)

                    gLock.acquire()
                    eventDict[event_name] = order_values
                    gLock.release()
                    print('**** Orbix Inplay Data ****')
                    print(order_values)
                sleep(0.01)
            except Exception as e:
                print(e)
                sleep(1)
                continue

    def scrapping(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_path = os.path.join(os.path.dirname(__file__), 'drivers', 'chromedriver')
        print('===>>> chrome_path = ', chrome_path)
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless")
        self.browser = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)
        # self.browser.maximize_window()
        self.login();
        sleep(10)
        self.scrapTennis()

    def start_thread(self):
        print('orbit_start_thread')
        self.isRunning = True
        scrapThread = threading.Thread(target=self.scrapping)
        scrapThread.start()
        print('orbit_start_thread return')

    def stop_thread(self):
        self.isRunning = False
        sleep(2)

        try:
            scrapThread.stop()
            del scrapThread
            print('orbit_Stopped')
        except:
            print('orbit_Stop Failed')
            pass


class MainWnd(QMainWindow):
    def __init__(self, parent=None):
        super(MainWnd, self).__init__(parent)

        self.b_IsRunningAlarm = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_Timer)

        # Implememt GUI
        layout = QVBoxLayout()

        lay_hor_1 = QHBoxLayout()
        self.btn_Scan = QPushButton("SCAN")
        self.btn_Close = QPushButton("CLOSE")

        self.btn_Scan.clicked.connect(self.on_btn_Scan_Clicked)
        self.btn_Close.clicked.connect(self.on_btn_Close_Clicked)

        lay_hor_1.addWidget(self.btn_Scan)
        lay_hor_1.addWidget(self.btn_Close)

        self.table_detail = QTableWidget()
        self.table_detail.setColumnCount(6)
        self.table_detail.setRowCount(2)
        header = self.table_detail.horizontalHeader()
        #
        # header.setSectionResizeMode(0, QHeaderView.Stretch)
        # header.setSectionResizeMode(1, QHeaderView.Stretch)
        # header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table_detail.horizontalHeader().setVisible(False)
        self.table_detail.verticalHeader().setVisible(False)

        self.table_detail.setSpan(0, 0, 2, 1)
        newItem = QTableWidgetItem('Event name')
        self.table_detail.setItem(0, 0, newItem)

        self.table_detail.setSpan(0, 1, 2, 1)
        newItem = QTableWidgetItem('Players Information')
        self.table_detail.setItem(0, 1, newItem)

        self.table_detail.setSpan(0, 2, 1, 2)
        newItem = QTableWidgetItem('sports.williamhill.it')
        newItem.setBackground(QtGui.QColor(255, 100, 100))
        self.table_detail.setItem(0, 2, newItem)

        self.table_detail.setSpan(0, 4, 1, 2)
        newItem = QTableWidgetItem('orbitexch.com')
        newItem.setBackground(QtGui.QColor(0, 0, 255))
        newItem.setForeground(QtGui.QColor(255, 255, 255))
        self.table_detail.setItem(0, 4, newItem)

        newItem = QTableWidgetItem('First Odds')
        self.table_detail.setItem(1, 2, newItem)
        newItem = QTableWidgetItem('Second Odds')
        self.table_detail.setItem(1, 3, newItem)

        newItem = QTableWidgetItem('First Odds')
        self.table_detail.setItem(1, 4, newItem)
        newItem = QTableWidgetItem('Second Odds')
        self.table_detail.setItem(1, 5, newItem)

        self.table_detail.setColumnHidden(0, True)
        self.table_detail.setColumnWidth(1, 350)
        self.table_detail.setColumnWidth(2, 80)
        self.table_detail.setColumnWidth(3, 80)
        self.table_detail.setColumnWidth(4, 80)
        self.table_detail.setColumnWidth(5, 80)

        layout.addLayout(lay_hor_1)
        layout.addWidget(self.table_detail)

        self.statusBar().showMessage('Ready')
        centralWnd = QWidget()
        centralWnd.setLayout(layout)
        self.setCentralWidget(centralWnd)
        self.setFixedSize(700, 500)
        self.setWindowTitle("SCRAP TENNIS ORDER")

    def on_btn_Scan_Clicked(self):
        if (self.btn_Scan.text() == 'SCAN'):
            threads.clear()
            eventDict.clear()

            threads['orbix'] = OrbixScraper()
            threads['orbix'].start_thread()

            threads['williamHill'] = WilliamHillScraper()
            threads['williamHill'].start_thread()

            self.timer.start(1000)
            self.statusBar().showMessage('Scraping.....')
            self.btn_Scan.setText('STOP')
            self.btn_Close.setEnabled(False)
        else:
            threads['williamHill'].stop_thread()
            threads['orbix'].stop_thread()

            self.timer.stop()
            self.statusBar().showMessage('Stopped.....')
            self.btn_Scan.setText('SCAN')
            self.btn_Close.setEnabled(True)

    def on_btn_Close_Clicked(self):
        sys.exit(1)

    def sound_alarm1(self):
        self.b_IsRunningAlarm = True
        playsound('SoundAlarm1.mp3')
        self.b_IsRunningAlarm = False

    def sound_alarm(self):
        self.b_IsRunningAlarm = True
        playsound('SoundAlarm.wav')
        self.b_IsRunningAlarm = False

    def set_Table_Data(self, eventName, eventStatus, orbix_1, orbix_2, william_1, william_2):
        numRows = self.table_detail.rowCount()
        insertIndex = -1

        try:
            for index in range(2, numRows):
                # print(self.table_detail.item(index, 0).text())
                if (self.table_detail.item(index, 0).text() == eventName):
                    insertIndex = index
                    break
            if (insertIndex == -1):
                self.table_detail.insertRow(numRows)
                insertIndex = numRows

            self.table_detail.setItem(insertIndex, 0, QTableWidgetItem(eventName))
            self.table_detail.setItem(insertIndex, 1, QTableWidgetItem(eventStatus))
            self.table_detail.setItem(insertIndex, 2, QTableWidgetItem(william_1))
            self.table_detail.setItem(insertIndex, 3, QTableWidgetItem(william_2))
            self.table_detail.setItem(insertIndex, 4, QTableWidgetItem(orbix_1))
            self.table_detail.setItem(insertIndex, 5, QTableWidgetItem(orbix_2))

        except:
            print('setTableData Exception')

        try:
            float_orbix_1 = float(orbix_1)
        except:
            float_orbix_1 = 0
        try:
            float_orbix_2 = float(orbix_2)
        except:
            float_orbix_2 = 0
        try:
            float_william_1 = float(william_1)
        except:
            float_william_1 = 0
        try:
            float_william_2 = float(william_2)
        except:
            float_william_2 = 0

        try:
            if (float_william_1 >= float_orbix_1):
                # Change cell background
                self.table_detail.item(insertIndex, 2).setBackground(QtGui.QColor(255, 255, 0))
                self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(255, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][0] = int(oddCompareDuration[eventName][0]) + 1
                else:
                    oddCompareDuration[eventName] = [1, 0]

                if self.b_IsRunningAlarm == False and int(oddCompareDuration[eventName][0]) >= 9 and \
                        float_william_1>= 1.3 and float_william_1 <= 21 and \
                        float_orbix_1 >= 1.3 and float_orbix_1 <= 21:
                    alarmThread = threading.Thread(target=self.sound_alarm)
                    alarmThread.start()
            else:
                self.table_detail.item(insertIndex, 2).setBackground(QtGui.QColor(0, 255, 0))
                self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(0, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][0] = 0
                else:
                    oddCompareDuration[eventName] = [0, 0]
        except:
            self.table_detail.item(insertIndex, 2).setBackground(QtGui.QColor(0, 255, 0))
            self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(0, 255, 0))
            if eventName in oddCompareDuration.keys():
                oddCompareDuration[eventName][0] = 0
            else:
                oddCompareDuration[eventName] = [0, 0]

        try:
            if (float_william_2 >= float_orbix_2):
                self.table_detail.item(insertIndex, 3).setBackground(QtGui.QColor(255, 255, 0))
                self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(255, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][1] = int(oddCompareDuration[eventName][1]) + 1
                else:
                    oddCompareDuration[eventName] = [0, 1]

                if self.b_IsRunningAlarm == False and int(oddCompareDuration[eventName][1]) >= 9 and \
                        float_william_2 >= 1.3 and float_william_2 <= 21 and \
                        float_orbix_2 >= 1.3 and float_orbix_2 <= 21:
                    alarmThread = threading.Thread(target=self.sound_alarm1)
                    alarmThread.start()
            else:
                self.table_detail.item(insertIndex, 3).setBackground(QtGui.QColor(0, 255, 0))
                self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(0, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][1] = 0
                else:
                    oddCompareDuration[eventName] = [0, 0]
        except:
            self.table_detail.item(insertIndex, 3).setBackground(QtGui.QColor(0, 255, 0))
            self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(0, 255, 0))
            if eventName in oddCompareDuration.keys():
                oddCompareDuration[eventName][1] = 0
            else:
                oddCompareDuration[eventName] = [0, 0]

    def on_Timer(self):
        if (self.b_IsRunningAlarm == True):
            return
        gLock.acquire()
        try:
            # print('eventDict Length: {0}', len(eventDict))
            for key, value in eventDict.items():
                if key in eventWilliamHillDict.keys() and len(value) >= 3 and len(eventWilliamHillDict[key]) >= 2:
                    self.set_Table_Data(key, value[0], value[1], value[2],
                                        eventWilliamHillDict[key][0], eventWilliamHillDict[key][1])
            gLock.release()
        except Exception as e:
            print('OnTimer Except:', e)
            gLock.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWnd()
    window.show()
    sys.exit(app.exec())
