# Created by BaiJiFeiLong@gmail.com at 2022/6/23
import ctypes
import json
import os
import sys
from pathlib import Path

import delegator
import pendulum
from PySide2 import QtWidgets, QtCore, QtGui


def logMessage(message):
    message = "[{}] {}".format(pendulum.now().isoformat(timespec="milliseconds", sep=" ")[:-6], message)
    lines = textBrowser.toPlainText().splitlines()
    lines = (lines + [message])[-10000:]
    textBrowser.setPlainText("\n".join(lines))
    textBrowser.verticalScrollBar().setValue(textBrowser.verticalScrollBar().maximum())
    mainWindow.repaint()


def requestUacOrSkip():
    ctypes.windll.shell32.IsUserAnAdmin() or ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1) > 32 and sys.exit()


def executeCommand(text):
    logMessage("Command: {}".format(text))
    command = delegator.run(text)
    logMessage("Command return code: {}".format(command.return_code))
    logMessage("Command stdout: {}".format(command.out or "<empty>"))
    logMessage("Command stderr: {}".format(command.err or "<empty>"))
    logMessage("Operation is {}".format("successful" if command.return_code == 0 else "failed"))
    return command.return_code


def isProtectDisabled():
    cmd = delegator.run("powershell Get-MpPreference | findstr DisableRealtimeMonitoring")
    disabled = cmd.out.split()[-1]
    assert disabled in ["True", "False"]
    return disabled == "True"


def doDisableProtect() -> bool:
    logMessage("Disabling protect...")
    if isProtectDisabled():
        logMessage("Already disabled.")
        return True
    return executeCommand("powershell Set-MpPreference -DisableRealtimeMonitoring $true") == 0


def doEnableProtect():
    logMessage("Enabling protect...")
    if not isProtectDisabled():
        logMessage("Already enabled.")
        return True
    return executeCommand("powershell Set-MpPreference -DisableRealtimeMonitoring $false") == 0


def updateConfig(**kwargs):
    for k, v in kwargs.items():
        config[k] = v
    configPath.write_text(json.dumps(config, indent=4))


def doToggleDefenderBlocker():
    requestUacOrSkip()
    if config["defenderBlockerOn"]:
        logMessage("Turning off defender blocker...")
        success = doEnableProtect()
        blockerCheckBox.setChecked(not success)
        if success:
            timer.isActive() and timer.stop()
            updateConfig(defenderBlockerOn=False)
    else:
        logMessage("Turning on defender blocker...")
        success = doDisableProtect()
        blockerCheckBox.setChecked(success)
        if success:
            timer.isActive() or timer.start(300_000)
            updateConfig(defenderBlockerOn=True)


def doToggleAutoStart():
    requestUacOrSkip()
    taskName = r"IceSpringDesktopHelper\AutoRun"
    if config["autoRun"]:
        logMessage("Disabling auto run...")
        template = r"schtasks /Delete /F /TN {}"
        commandText = template.format(taskName)
        success = executeCommand(commandText) == 0
        autoRunCheckBox.setChecked(not success)
        if success:
            updateConfig(autoRun=False)
            logMessage("Auto run disabled")
    else:
        logMessage("Enabling auto run...")
        template = r"schtasks /Create /F /SC ONLOGON /RL HIGHEST /TN {} /TR {}"
        commandText = template.format(taskName, sys.executable)
        success = executeCommand(commandText) == 0
        autoRunCheckBox.setChecked(success)
        if success:
            updateConfig(autoRun=True)
            logMessage("Auto run enabled")


def onTrayIconActivated(_type):
    if _type == QtWidgets.QSystemTrayIcon.Trigger:
        mainWindow.show()
    elif _type == QtWidgets.QSystemTrayIcon.Context:
        menu = QtWidgets.QMenu()
        menu.addAction("Exit", lambda: sys.exit())
        menu.exec_(QtGui.QCursor.pos())


os.chdir(Path(__file__).parent)
app = QtWidgets.QApplication()
app.setApplicationName("Ice Spring Desktop Helper")
app.setApplicationDisplayName(app.applicationName())
app.setWindowIcon(QtGui.QIcon("resources/logo.ico"))
font = app.font()
font.setPointSize(int(font.pointSize() * 1.25))
app.setFont(font)
mainWindow = QtWidgets.QMainWindow()
autoRunCheckBox = QtWidgets.QCheckBox("Auto Run")
autoRunCheckBox.clicked.connect(doToggleAutoStart)
blockerCheckBox = QtWidgets.QCheckBox("Microsoft Defender Blocker")
blockerCheckBox.clicked.connect(doToggleDefenderBlocker)
textBrowser = QtWidgets.QTextBrowser()
mainWidget = QtWidgets.QWidget(mainWindow)
rootLayout = QtWidgets.QVBoxLayout(mainWidget)
rootLayout.addWidget(autoRunCheckBox)
rootLayout.addWidget(blockerCheckBox)
rootLayout.addWidget(textBrowser)
mainWindow.setCentralWidget(mainWidget)
mainWindow.resize(854, 480)
mainWindow.closeEvent = lambda x: x.ignore() or mainWindow.hide()

trayIcon = QtWidgets.QSystemTrayIcon(app.windowIcon(), app)
trayIcon.activated.connect(onTrayIconActivated)

timer = QtCore.QTimer(app)
timer.timeout.connect(doDisableProtect)

configPath = Path("config.json")
if not configPath.exists():
    configPath.write_text(json.dumps(dict(defenderBlockerOn=False, autoRun=False), indent=4))
config = json.loads(configPath.read_text())


def applyConfig():
    if config["defenderBlockerOn"]:
        blockerCheckBox.setChecked(True)
        config["defenderBlockerOn"] = False
        doToggleDefenderBlocker()
    if config["autoRun"]:
        autoRunCheckBox.setChecked(True)


def main():
    logMessage("Starting...")
    applyConfig()
    trayIcon.show()
    logMessage("Ready.")
    app.exec_()


if __name__ == '__main__':
    main()
