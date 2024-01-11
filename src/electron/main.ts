// electron/electron.js
import { app, BrowserWindow, ipcMain } from 'electron'
import * as path from 'path'
import { fileURLToPath } from 'url'

//es6获取绝对路径
const __dirname = path.dirname(fileURLToPath(import.meta.url))

app.commandLine.appendSwitch('lang', 'zh-CN')

//es6判断是否开发环境
const isDev = import.meta.env.MODE === 'development' ? true : false;

function createWindow() {
    // Create the browser window.
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.ts')
        },
    });

    // and load the index.html of the app.
    // win.loadFile("index.html");
    mainWindow.loadURL(
        isDev
            ? 'http://localhost:5173/'
            : `file://${path.join(__dirname, '../dist/index.html')}`
    );
    // 开发环境打开 DevTools
    if (isDev) {
        mainWindow.webContents.openDevTools();
    }
}

// 当 Electron 完成时，将调用此方法初始化并准备创建浏览器窗口。某些 API 只能在发生此事件后使用。
app.whenReady().then(() => {
    createWindow()
    app.on('activate', function () {
        // 在 macos 上，通常会在应用程序中重新创建一个窗口，当单击停靠图标，并没有打开其他窗口。
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })

});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
    // if (process.platform !== 'darwin') {
        app.quit();
    // }
});
