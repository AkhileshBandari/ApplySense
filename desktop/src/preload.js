const { contextBridge, ipcRenderer } = require('electron');

contextBridge.revealInMainWorld('applysenseAPI', {
  getLocalApps: () => ipcRenderer.invoke('get-local-apps'),
  addLocalApp: (appData) => ipcRenderer.invoke('add-local-app', appData)
});
