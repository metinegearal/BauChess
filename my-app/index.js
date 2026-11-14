const { app, BrowserWindow } = require('electron');
const path = require('node:path');
const { spawn } = require('node:child_process');

let backendProcess;
function createWindow() {
  const win = new BrowserWindow({
    width: 1400, height: 900,
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });
  win.loadFile(path.join(__dirname, 'dist/index.html'));
}
app.whenReady().then(() => {
  backendProcess = spawn(process.execPath, [path.join(__dirname, 'backend.js')], {
    env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }, stdio: 'inherit',
  });
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
app.on('before-quit', () => backendProcess?.kill());
