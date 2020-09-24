import os
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from PyQt5 import QtGui
from playsound import playsound

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
eventBet365Dict = {}
eventWilliamHillDict = {}
oddCompareDuration = {}
gLock = threading.Lock()
scrapThread = None
bet365Thread = None
williamHillThread = None


############################

class BetmantraScraper():
    def __init__(self):
        self.current_url = ''
        self.isRunning = False
        self.browser = None
        self.main_url = 'https://betmantra.com/home/highlights/tennis'
        self.user_name = 'LucaD1'
        self.password = 'aaabbb111'

    def login(self):
        print('=== Starting login ===')
        username_input = self.browser.find_element_by_id('username')
        password_input = self.browser.find_element_by_id('password')
        self.browser.execute_script("arguments[0].setAttribute('value','" + self.user_name + "')", username_input)
        self.browser.execute_script("arguments[0].setAttribute('value','" + self.password + "')", password_input)
        login_button = self.browser.find_element_by_id('check2faBtn')
        login_button.click()
        print('=== Finished login ===')

    def hasDisabledClass(self, element):
        return 'disabled' in element.get_attribute('class')

    def scrapTennis(self):
        print('=== Starting tennis scrapping ===')

        while self.isRunning:
            try:
                inplay_block = self.browser.find_element_by_css_selector('.inPlay-item-outer.row.ng-scope.table-header')
                rows = inplay_block.find_elements_by_css_selector(
                    '.inPlay-item-inner.inPlay-inner-market.col-xs-12.no-draw-column')
                for row in rows:
                    # get event name first
                    event_container_inner = row.find_element_by_class_name('event-name-container-inner')
                    market_selection = event_container_inner.find_element_by_class_name('market-selection')
                    event_status = ''

                    try:
                        event_name_left = market_selection.find_element_by_class_name('event-name-link-text-left')
                        event_name_right = market_selection.find_element_by_class_name('event-name-link-text-right')
                        event_status = event_name_left.text + ' ' + event_name_right.text
                    except:
                        event_name = market_selection.find_element_by_class_name('event-name-link-text')
                        event_status = event_name.text

                    try:
                        event_live_score = market_selection.find_element_by_class_name('live-score-score')
                        event_status += ' ' + event_live_score.text
                    except:
                        None

                    event_name = str(market_selection.get_attribute('href'))

                    try:
                        suspended_div = row.find_element_by_css_selector('.suspended.ng-hide')
                        # this match is suspended
                    except:
                        # print('not suspended')
                        # get bet lay values
                        bet_cols = row.find_elements_by_css_selector('.digitItemInner.col-xs-12.ng-scope')
                        order_values = []

                        # append player information and score
                        order_values.append(event_status)

                        # append order values
                        for bet_section in bet_cols:
                            if (self.hasDisabledClass(bet_section)):
                                continue
                            lay_span = bet_section.find_element_by_css_selector('.lay.col-xs-6.ng-scope')
                            lay_a = lay_span.find_element_by_class_name('bet-selection')
                            order_values.append(str(lay_a.text))

                        # add 2 elements instead of bet365 scrap result
                        # order_values.append('')
                        # order_values.append('')

                        gLock.acquire()
                        eventDict[event_name] = order_values
                        # print('order_values' + str(order_values))
                        gLock.release()

            except Exception as inst:
                # print('error ' + str(type(inst)) + ', '.join(str(x) for x in inst.args))
                try:
                    self.browser.find_element_by_id('username')
                    self.login()
                    sleep(7)
                    self.browser.get(self.main_url)
                    sleep(3)
                except:
                    None
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
        sleep(3)
        self.login()
        sleep(10)
        self.scrapTennis()

    def start_thread(self):
        print('betmantra_start_thread')
        self.isRunning = True
        scrapThread = threading.Thread(target=self.scrapping)
        scrapThread.start()
        print('betmantra_start_thread return')

    def stop_thread(self):
        self.isRunning = False
        sleep(2)

        try:
            scrapThread.stop()
            del scrapThread
            print('betmantra_Stopped')
        except:
            print('betmantra_Stop Failed')
            pass


class Bet365Api():
    def __init__(self):
        self.token = '33849-jRYZx3H2UQQjLk'
        self.isRunning = False

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

    def getOdds(self):
        print('=== Starting Bet365 Api GetOdds ===')
        while self.isRunning:
            try:
                eventBet365Dict.clear()
                inplay_url = "https://api.betsapi.com/v1/events/inplay"
                querystring = {"sport_id": "13", "token": self.token}
                response = requests.request("GET", inplay_url, params=querystring)
                inplay_data = response.json()
                results = inplay_data['results']
                for result in results:
                    event_id = result['id']
                    home_name = result['home']['name']
                    away_name = result['away']['name']
                    common_eventname = self.getCommonEventName(home_name, away_name)
                    if common_eventname == '':
                        continue

                    odds_url = "https://api.betsapi.com/v2/event/odds"
                    odds_querystring = {"token": self.token, "event_id": event_id, "odds_market": "1"}
                    odds_response = requests.request("GET", odds_url, params=odds_querystring)
                    odds_data = odds_response.json()

                    home_odds = odds_data['results']['odds']['13_1'][0]['home_od']
                    away_odds = odds_data['results']['odds']['13_1'][0]['away_od']

                    # print(home_odds)
                    # print(away_odds)

                    odds_values = [home_odds, away_odds]
                    eventBet365Dict[common_eventname] = odds_values
            except:
                None
            sleep(2)

    def start_thread(self):
        print('bet365_start_thread')
        self.isRunning = True
        bet365Thread = threading.Thread(target=self.getOdds)
        bet365Thread.start()
        print('bet365_start_thread return')

    def stop_thread(self):
        self.isRunning = False
        sleep(2)

        try:
            bet365Thread.stop()
            del bet365Thread
            print('bet365_Stopped')
        except:
            print('bet365_Stop Failed')
            pass


class WilliamHillScraper():
    def __init__(self):
        self.current_url = ''
        self.isRunning = False
        self.browser = None
        self.main_url = 'http://sports.williamhill.it/bet_ita/it/betting/y/17/Tennis.html'

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
                inplay_block = self.browser.find_element_by_id('ip_type_0_mkt_grps')
                rows = inplay_block.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
                for row in rows:
                    # get event name first
                    if row.value_of_css_property("display") == "none":
                        continue
                    event_name = row.find_element_by_class_name('CentrePad').find_element_by_tag_name('span').text

                    home_name = event_name.split('-')[0]
                    away_name = event_name.split('-')[1]
                    common_eventname = self.getCommonEventName(home_name, away_name)
                    if common_eventname == '':
                        continue

                    td_elements = row.find_elements_by_tag_name('td')

                    home_odds = td_elements[3].find_element_by_tag_name('div').find_element_by_tag_name('div').text
                    away_odds = td_elements[5].find_element_by_tag_name('div').find_element_by_tag_name('div').text

                    odds_values = [home_odds, away_odds]
                    eventWilliamHillDict[common_eventname] = odds_values

            except Exception as inst:
                # print('error ' + str(type(inst)) + ', '.join(str(x) for x in inst.args))
                continue

    def scrapping(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_path = os.path.join(os.path.dirname(__file__), 'drivers', 'chromedriver')
        print('===>>> chrome_path = ', chrome_path)
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless")
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
        self.table_detail.setColumnCount(8)
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
        newItem = QTableWidgetItem('bet365.com')
        newItem.setBackground(QtGui.QColor(0, 255, 0))
        self.table_detail.setItem(0, 2, newItem)

        self.table_detail.setSpan(0, 4, 1, 2)
        newItem = QTableWidgetItem('betmantra.com')
        newItem.setBackground(QtGui.QColor(255, 100, 100))
        self.table_detail.setItem(0, 4, newItem)

        self.table_detail.setSpan(0, 6, 1, 2)
        newItem = QTableWidgetItem('sports.williamhill.it')
        newItem.setBackground(QtGui.QColor(0, 0, 255))
        newItem.setForeground(QtGui.QColor(255, 255, 255))
        self.table_detail.setItem(0, 6, newItem)

        newItem = QTableWidgetItem('First Odds')
        self.table_detail.setItem(1, 2, newItem)
        newItem = QTableWidgetItem('Second Odds')
        self.table_detail.setItem(1, 3, newItem)

        newItem = QTableWidgetItem('First Odds')
        self.table_detail.setItem(1, 4, newItem)
        newItem = QTableWidgetItem('Second Odds')
        self.table_detail.setItem(1, 5, newItem)

        newItem = QTableWidgetItem('First Odds')
        self.table_detail.setItem(1, 6, newItem)
        newItem = QTableWidgetItem('Second Odds')
        self.table_detail.setItem(1, 7, newItem)

        self.table_detail.setColumnHidden(0, True)
        self.table_detail.setColumnWidth(1, 200)
        self.table_detail.setColumnWidth(2, 80)
        self.table_detail.setColumnWidth(3, 80)
        self.table_detail.setColumnWidth(4, 80)
        self.table_detail.setColumnWidth(5, 80)
        self.table_detail.setColumnWidth(6, 80)
        self.table_detail.setColumnWidth(7, 80)

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

            threads['betmantra'] = BetmantraScraper()
            threads['betmantra'].start_thread()

            threads['bet365api'] = Bet365Api()
            threads['bet365api'].start_thread()

            threads['williamHill'] = WilliamHillScraper()
            threads['williamHill'].start_thread()

            self.timer.start(3000)
            self.statusBar().showMessage('Scraping.....')
            self.btn_Scan.setText('STOP')
            self.btn_Close.setEnabled(False)
        else:
            threads['betmantra'].stop_thread()
            threads['bet365api'].stop_thread()

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

    def set_Table_Data(self, eventName, eventStatus, betmantra_1, betmantra_2, bet365_1, bet365_2, william_1, william_2):
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
            self.table_detail.setItem(insertIndex, 2, QTableWidgetItem(bet365_1))
            self.table_detail.setItem(insertIndex, 3, QTableWidgetItem(bet365_2))
            self.table_detail.setItem(insertIndex, 4, QTableWidgetItem(betmantra_1))
            self.table_detail.setItem(insertIndex, 5, QTableWidgetItem(betmantra_2))
            self.table_detail.setItem(insertIndex, 6, QTableWidgetItem(william_1))
            self.table_detail.setItem(insertIndex, 7, QTableWidgetItem(william_2))
        except:
            print('setTableData Exception')

        float_betmantra_1 = 0
        float_betmantra_2 = 0
        float_bet365_1 = 0
        float_bet365_2 = 0
        float_william_1 = 0
        float_william_2 = 0
        
        try:
            float_betmantra_1 = float(betmantra_1)
        except:
            float_betmantra_1 = 0
        try:
            float_betmantra_2 = float(betmantra_2)
        except:
            float_betmantra_2 = 0
        try:
            float_bet365_1 = float(bet365_1)
        except:
            float_bet365_1 = 0
        try:
            float_bet365_2 = float(bet365_2)
        except:
            float_bet365_2 = 0
        try:
            float_william_1 = float(william_1)
        except:
            float_william_1 = 0
        try:
            float_william_2 = float(william_2)
        except:
            float_william_2 = 0
        try:
            if (float_bet365_1 >= float_betmantra_1):
                self.table_detail.item(insertIndex, 2).setBackground(QtGui.QColor(255, 0, 0))
                self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(255, 0, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][0] = int(oddCompareDuration[eventName][0]) + 1
                else:
                    oddCompareDuration[eventName] = [1, 0, 0, 0]

                if self.b_IsRunningAlarm == False and int(oddCompareDuration[eventName][0]) >= 4 and \
                        float(bet365_1) >= 1.3 and float(bet365_1) <= 21 and \
                        float(betmantra_1) >= 1.3 and float(betmantra_1) <= 21:
                    alarmThread = threading.Thread(target=self.sound_alarm)
                    alarmThread.start()
            else:
                self.table_detail.item(insertIndex, 2).setBackground(QtGui.QColor(0, 255, 0))
                self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(0, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][0] = 0
                else:
                    oddCompareDuration[eventName] = [0, 0, 0, 0]
        except:
            self.table_detail.item(insertIndex, 2).setBackground(QtGui.QColor(0, 255, 0))
            self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(0, 255, 0))
            if eventName in oddCompareDuration.keys():
                oddCompareDuration[eventName][0] = 0
            else:
                oddCompareDuration[eventName] = [0, 0, 0, 0]

        try:
            if (float_bet365_2 >= float_betmantra_2):
                self.table_detail.item(insertIndex, 3).setBackground(QtGui.QColor(255, 0, 0))
                self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(255, 0, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][1] = int(oddCompareDuration[eventName][1]) + 1
                else:
                    oddCompareDuration[eventName] = [0, 1, 0, 0]

                if self.b_IsRunningAlarm == False and int(oddCompareDuration[eventName][1]) >= 4 and \
                        float(bet365_2) >= 1.3 and float(bet365_2) <= 21 and \
                        float(betmantra_2) >= 1.3 and float(betmantra_2) <= 21:
                    alarmThread = threading.Thread(target=self.sound_alarm)
                    alarmThread.start()
            else:
                self.table_detail.item(insertIndex, 3).setBackground(QtGui.QColor(0, 255, 0))
                self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(0, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][1] = 0
                else:
                    oddCompareDuration[eventName] = [0, 0, 0, 0]
        except:
            self.table_detail.item(insertIndex, 3).setBackground(QtGui.QColor(0, 255, 0))
            self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(0, 255, 0))
            if eventName in oddCompareDuration.keys():
                oddCompareDuration[eventName][1] = 0
            else:
                oddCompareDuration[eventName] = [0, 0, 0, 0]


        try:
            if (float_william_1 >= float_betmantra_1):
                if (float_bet365_1 < float_betmantra_1):
                    self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(255, 255, 0))
                self.table_detail.item(insertIndex, 6).setBackground(QtGui.QColor(255, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][2] = int(oddCompareDuration[eventName][0]) + 1
                else:
                    oddCompareDuration[eventName] = [0, 0, 1, 0]

                if self.b_IsRunningAlarm == False and int(oddCompareDuration[eventName][2]) >= 4 and \
                        float(william_1) >= 1.3 and float(william_1) <= 21 and \
                        float(betmantra_1) >= 1.3 and float(betmantra_1) <= 21:
                    alarmThread = threading.Thread(target=self.sound_alarm1)
                    alarmThread.start()
            else:
                if (float_bet365_1 < float_betmantra_1):
                    self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(0, 255, 0))
                self.table_detail.item(insertIndex, 6).setBackground(QtGui.QColor(0, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][2] = 0
                else:
                    oddCompareDuration[eventName] = [0, 0, 0, 0]
        except:
            if (float_bet365_1 < float_betmantra_1):
                self.table_detail.item(insertIndex, 4).setBackground(QtGui.QColor(0, 255, 0))
            self.table_detail.item(insertIndex, 6).setBackground(QtGui.QColor(0, 255, 0))
            if eventName in oddCompareDuration.keys():
                oddCompareDuration[eventName][2] = 0
            else:
                oddCompareDuration[eventName] = [0, 0, 0, 0]

        try:
            if (float_william_2 >= float_betmantra_2):
                if (float_bet365_2 < float_betmantra_2):
                    self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(255, 255, 0))
                self.table_detail.item(insertIndex, 7).setBackground(QtGui.QColor(255, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][3] = int(oddCompareDuration[eventName][1]) + 1
                else:
                    oddCompareDuration[eventName] = [0, 0, 0, 1]

                if self.b_IsRunningAlarm == False and int(oddCompareDuration[eventName][3]) >= 4 and \
                        float(william_2) >= 1.3 and float(william_2) <= 21 and \
                        float(betmantra_2) >= 1.3 and float(betmantra_2) <= 21:
                    alarmThread = threading.Thread(target=self.sound_alarm1)
                    alarmThread.start()
            else:
                if (float_bet365_2 < float_betmantra_2):
                    self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(0, 255, 0))
                self.table_detail.item(insertIndex, 7).setBackground(QtGui.QColor(0, 255, 0))
                if eventName in oddCompareDuration.keys():
                    oddCompareDuration[eventName][3] = 0
                else:
                    oddCompareDuration[eventName] = [0, 0, 0, 0]
        except:
            if (float_bet365_2 < float_betmantra_2):
                self.table_detail.item(insertIndex, 5).setBackground(QtGui.QColor(0, 255, 0))
            self.table_detail.item(insertIndex, 7).setBackground(QtGui.QColor(0, 255, 0))
            if eventName in oddCompareDuration.keys():
                oddCompareDuration[eventName][3] = 0
            else:
                oddCompareDuration[eventName] = [0, 0, 0, 0]

    def on_Timer(self):
        if (self.b_IsRunningAlarm == True):
            return
        gLock.acquire()
        try:
            # print('eventDict Length: {0}', len(eventDict))
            for key, value in eventDict.items():
                if key in eventBet365Dict.keys() and key in eventWilliamHillDict.keys() and len(value) >= 3 and \
                        len(eventBet365Dict[key]) >= 2 and len(eventWilliamHillDict[key]) >= 2:
                    self.set_Table_Data(key, value[0], value[1], value[2],
                                        eventBet365Dict[key][0], eventBet365Dict[key][1],
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
