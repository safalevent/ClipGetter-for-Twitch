import requests
import ast
import PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui
from ui import Ui_MainWindow
from tkinter import Tk
import urllib.request
from PyQt5.QtCore import QDate
from threading import Thread

import resources_rc

class mainWindow(QtWidgets.QMainWindow):
    #Client ID and Client Secret will be given to you when you register your app to Twitch.
    client_id = "YOU CLIENT ID HERE"
    client_secret = "YOUR CLIENT SECRET HERE"

    data = []
    token = None
    
    dateStart = None
    dateEnd = None

    def __init__(self):
        super(mainWindow,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.refreshList)
        self.ui.pushButton_2.clicked.connect(self.clipInfoGetter)
        self.ui.pushButton_3.clicked.connect(self.copyLink)
        self.ui.broadcasterName.setPlaceholderText("Streamer Name")
        self.ui.clipName.setPlaceholderText("Clip Name")
        self.ui.dateStart.dateChanged.connect(self.onDateStartChanged)
        self.ui.dateEnd.dateChanged.connect(self.onDateEndChanged)
        self.loadingChanger("")

        self.getToken()

    def copyLink(self):
        if len(self.ui.listWidget.selectedItems()) != 0:
            index = self.ui.listWidget.currentRow()
            url=self.data[index]["url"]
            tk = Tk()
            tk.withdraw()
            tk.clipboard_clear()
            tk.clipboard_append(url)
            tk.update()
            tk.destroy()

    def loadingChanger(self,something):
        self.ui.loading.setText(something)

    def changeImage(self,url):
        try:
            data = urllib.request.urlopen(url).read()
            image = PyQt5.QtGui.QImage()
            image.loadFromData(data)
            self.ui.clipImage.setPixmap(PyQt5.QtGui.QPixmap(image).scaledToWidth(121))
        except (urllib.error.HTTPError, ValueError, urllib.error.URLError) as ex:
            if type(ex) != ValueError: #ValueError will be raised when this function is called with url = "".
                print("Exception happened while taking image from Twitch.")

            image = PyQt5.QtGui.QImage(":/noClipImage/noClipImage.jpg")
            self.ui.clipImage.setPixmap(PyQt5.QtGui.QPixmap(image).scaledToWidth(121))

    def clipInfoGetter(self):
        if len(self.ui.listWidget.selectedItems()) != 0:
            index = self.ui.listWidget.currentRow()
            clip = self.data[index]

            #Programmer can add code here to happen when user clicks "Get Clip Information".
            
            self.ui.showClipName.setText(clip["title"])
            self.changeImage("")
            change_image_thread = Thread(target = self.changeImage, args = (clip["thumbnail_url"],))
            change_image_thread.start()
            
            table = self.ui.tableWidget
            table.setColumnCount(2)
            table.setColumnWidth(0,100)
            table.setColumnWidth(1,200)
            table.setRowCount(len(clip))

            for index in range(len(clip)):
                table.setItem(index, 0, QtWidgets.QTableWidgetItem(str(list(clip.keys())[index])))
                table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(list(clip.values())[index])))

    def getToken(self):
        client_id = self.client_id
        client_secret = self.client_secret
        grant_type = "client_credentials"
        token = requests.post("https://id.twitch.tv/oauth2/token?client_id=" + client_id + "&client_secret=" + client_secret + "&grant_type=" + grant_type)
        if token.status_code == 400:
            exit("Couldn't get a valid token from Twitch. Please check your client_id and client_secret.\nCurrent client id: " + client_id + "\nCurrent client secret: " + client_secret)
        self.token = ast.literal_eval(token.content.decode("utf-8"))["access_token"]

    def refreshList(self):
        self.loadingChanger("Searching...")
        self.ui.label_2.move(251,520)
        self.ui.label_2.setText("Clips")

        headers = {'Authorization': "Bearer "+ self.token, "Client-ID": self.client_id}
        self.ui.listWidget.clear()
        self.data = []
        
        try:
            broadcasterName = self.ui.broadcasterName.text().lower()
            broadcasterData = ast.literal_eval(requests.get("https://api.twitch.tv/helix/users?login=" + broadcasterName, headers=headers).content.decode("utf-8"))

            broadcasterData = broadcasterData["data"]
            if (broadcasterData == []):
                raise KeyError()
            broadcaster_id = broadcasterData[0]["id"]
            
            get_clip_thread = Thread(target = self.getClips, args = (headers, broadcaster_id))
            get_clip_thread.start()

        except (KeyError):
            self.loadingChanger("Streamer not found.")

    def getClips(self, headers, broadcaster_id):
        pagination = {"cursor":None}
        while(True):
            url = "https://api.twitch.tv/helix/clips?broadcaster_id="+broadcaster_id+"&first=100"
        
            if (self.dateStart != None and self.dateEnd != None):
                if (self.dateStart.daysTo(self.dateEnd)<0):
                    self.loadingChanger("Start date cannot exceed the end date.")
                    return

                date = self.ui.dateStart.date()
                startDate = str(date.year())+"-{:02d}".format(date.month())+"-{:02d}".format(date.day())+"T00:00:00Z"
                date = self.ui.dateEnd.date()
                endDate = str(date.year())+"-{:02d}".format(date.month())+"-{:02d}".format(date.day())+"T00:00:00Z"
                print("Searching from",startDate,"to",endDate)
                url = "https://api.twitch.tv/helix/clips?broadcaster_id="+broadcaster_id+"&first=100"+"&started_at="+startDate+"&ended_at="+endDate

            if pagination.get("cursor") != None:
                url += "&after="+pagination.get("cursor")

            response = requests.get(url, headers=headers)
            tempData = ast.literal_eval(response.content.decode("utf-8"))

            pagination = tempData["pagination"]
            tempData = tempData["data"] 

            for index in range(len(tempData)):
                clip = tempData[index]
                if self.ui.clipName.text().lower() in clip["title"].lower():
                    self.ui.listWidget.addItem(clip["title"])
                    self.data.append(clip)
        
            if len(self.data) != 0:
                length = str(len(self.data))
            else:
                length = "No"
            self.ui.label_2.setText(length + " clips found.")
            self.ui.label_2.move(170,520)

            if(pagination.get("cursor") == None):
                break

        self.loadingChanger("")

    def onDateStartChanged(self, newDate):
        if (newDate.daysTo(QDate(2006,9,18)) < 0):
            self.dateStart = newDate
        else:
            self.dateStart = None

    def onDateEndChanged(self, newDate):
        self.dateEnd = newDate

app = QtWidgets.QApplication([])
window = mainWindow()
window.show()
app.exec()