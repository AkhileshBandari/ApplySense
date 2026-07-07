const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

let mainWindow;
let db;

function initializeDatabase() {
  const dbPath = path.join(app.getPath('userData'), 'applysense_local.db');
  db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
      console.error('Failed to open local SQLite DB', err);
      return;
    }
    console.log('Opened offline SQLite database at:', dbPath);
    
    // Create baseline tables for offline mode sync
    db.run(`
      CREATE TABLE IF NOT EXISTS local_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        portal_type TEXT,
        status TEXT,
        match_score INTEGER,
        applied_at TEXT
      )
    `);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "ApplySense AI - Desktop Career OS",
    backgroundColor: '#090a0f',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load the web app dev server (or built files)
  mainWindow.loadURL('http://localhost:3000');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  initializeDatabase();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (db) db.close();
    app.quit();
  }
});

// IPC handlers for local database sync
ipcMain.handle('get-local-apps', async () => {
  return new Promise((resolve, reject) => {
    db.all("SELECT * FROM local_applications", [], (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
});

ipcMain.handle('add-local-app', async (event, appData) => {
  retur
<truncated 481 bytes>
