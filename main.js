const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 750,
    icon: path.join(__dirname, "assets/icon.svg"),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    title: "Cursor 账号切换助手",
  });

  win.loadFile("index.html");
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// 处理与 Python 的交互
function runPython(args) {
  return new Promise((resolve, reject) => {
    const pythonPath = "python3";
    // 在生产环境中，资源位于 Resources 目录下
    const scriptPath = app.isPackaged
      ? path.join(process.resourcesPath, "cursor_manager.py")
      : path.join(__dirname, "cursor_manager.py");

    const child = spawn(pythonPath, [scriptPath, ...args]);

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    child.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    child.on("close", (code) => {
      if (code === 0) {
        resolve(stdout.trim());
      } else {
        reject(stderr || `Process exited with code ${code}`);
      }
    });
  });
}

ipcMain.handle("get-status", async () => {
  const result = await runPython(["status_json"]);
  return JSON.parse(result);
});

ipcMain.handle("get-list", async () => {
  const result = await runPython(["list_json"]);
  return JSON.parse(result);
});

ipcMain.handle("switch-profile", async (event, name) => {
  return await runPython(["switch", name]);
});

ipcMain.handle("save-profile", async (event, name) => {
  return await runPython(["save", name]);
});

ipcMain.handle("reset-account", async () => {
  return await runPython(["reset"]);
});

ipcMain.handle("export-profiles", async () => {
  const { filePath } = await dialog.showSaveDialog({
    filters: [{ name: "Zip Files", extensions: ["zip"] }],
  });
  if (filePath) {
    return await runPython(["export", filePath]);
  }
  return null;
});

ipcMain.handle("import-profiles", async () => {
  const { filePaths } = await dialog.showOpenDialog({
    filters: [{ name: "Zip Files", extensions: ["zip"] }],
  });
  if (filePaths && filePaths.length > 0) {
    return await runPython(["import", filePaths[0]]);
  }
  return null;
});

ipcMain.handle("delete-profile", async (event, name) => {
  return await runPython(["delete", name]);
});

ipcMain.handle("delete-profiles", async (event, names) => {
  const results = [];
  for (const name of names) {
    results.push(await runPython(["delete", name]));
  }
  return results;
});
