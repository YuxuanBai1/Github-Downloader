[中文](README.CN.md) 

# Github-Downloader Introduction

Github-Downloader is a graphical GitHub accelerated download tool developed based on PyQt5. It accelerates GitHub file downloads through multiple proxy servers, supports multi-threaded downloads, and displays real-time speed. The tool features a clean and beautiful interface, intuitive operation, and supports cross-platform usage.

## ✨ Core Features

- 🚀 **Multi-Proxy Support**: Integrates acceleration proxies such as ghfast.top and gh-proxy.net, also supports direct download
- 🔄 **Multi-threaded Download**: Supports 1-16 download threads, significantly improving download speed
- 📊 **Real-time Monitoring**: Displays download progress, speed, and file size with intuitive progress bar
- 📝 **Detailed Logs**: Operation logs with timestamps and color coding for easy debugging and tracking
- 💾 **History Record**: Automatically saves download history, retains up to 100 records
- 🛠️ **Smart Parsing**: Automatically extracts filenames from GitHub links, supports multiple link formats
- ⏸️ **Download Control**: Can stop ongoing download tasks at any time

## 📋 System Requirements

- Python 3.6 or higher
- Windows/macOS/Linux operating system
- Normal network connection

## 🚀 Installation Steps

### 1. Clone the Project

```bash
git clone https://github.com/YuxuanBai1/Github-Downloader.git
cd Github-Downloader
```

### 2. Install Dependencies

```bash
pip install PyQt5 requests threading
```

## 📖 User Guide

### 1. Run the Program

Run the main program directly:

```bash
python github-downloader.py
```

### 2. Interface Layout

| Section                   | Function Description                                         |
| ------------------------- | ------------------------------------------------------------ |
| **Title Bar**             | Displays program name "GitHub Downloader"                    |
| **Speed Display Area**    | Shows real-time download speed and progress percentage       |
| **Download Link Area**    | Select proxy type and input GitHub file link                 |
| **Progress Display Area** | Shows download progress bar, downloaded/total size, and status information |
| **Settings Area**         | Set number of download threads (1-16) and select save path   |
| **Control Buttons Area**  | Start download and stop download buttons                     |
| **Log Area**              | Displays detailed operation logs, can be cleared             |

### 3. Operation Steps

1. **Input Download Link**
   - Paste GitHub file link in the download link input box
   - Example: `https://github.com/YuxuanBai1/Luogu-Plus/releases/download/v1.0.1/Luogu.Plus.crx`

2. **Select Proxy Server**
   - `ghfast.top`: Recommended GitHub acceleration proxy
   - `gh-proxy.net`: Alternative acceleration proxy
   - `Direct`: Download without proxy (may be slower)

3. **Set Download Parameters**
   - Drag slider to set number of threads (1-16, default is 4)
   - Click "Browse" button to select file save location (default is download folder)

4. **Start Download**
   - Click "Start Download" button to begin download task
   - View real-time download progress and speed
   - Can click "Stop Download" button to abort task at any time

5. **View Results**
   - Successful download will show "Download Complete" status
   - Download logs record all operation information
   - Files are saved in the specified location

## 🔧 Supported Link Formats

- Release files: `https://github.com/user/repository/releases/download/version/filename`
- Raw files: `https://raw.githubusercontent.com/user/repository/branch/path`
- Code archives: `https://codeload.github.com/user/repository/format/branch`
- Repository homepage: `https://github.com/user/repository`

## ⚠️ Precautions

1. **Network Connection**: Ensure network can normally access the selected proxy server
2. **File Permissions**: Ensure you have write permission to the selected save folder
3. **Link Format**: Input complete GitHub file links, the program will automatically process acceleration
4. **Thread Settings**: Too many threads may be limited by servers, recommended 4-8 threads
5. **Temporary Files**: Temporary files are generated in the target folder during download and are automatically merged and deleted after completion

## 🔍 Frequently Asked Questions

### Q: What should I do if download speed is very slow?

A: Try switching to different proxy servers, or adjust the number of download threads. In some network environments, direct connection may be faster.

### Q: What should I do if an error occurs during download?

A: Check network connection, ensure proxy server is available, then restart the download. Temporary files will be automatically cleaned.

### Q: What should I do if the interface displays abnormally after starting the program?

A: Ensure correct dependency libraries are installed: `pip install PyQt5 requests threading`

### Q: What should I do if unable to get file size or link is invalid?

A: Check if the input GitHub link is valid, ensure the file exists and is accessible.

### Q: What should I do if download completes but cannot find the file?

A: Check the set save path, ensure you have write permission. Files are saved with original filenames.

## 📄 License

This project is open source under the MIT License, can be freely modified, distributed, and used commercially. See LICENSE file for details.

## 🤝 Contribution

Welcome to submit Issues and Pull Requests to improve this project.

**Note**: This project is for learning and personal use only, please comply with GitHub's terms of service and the usage regulations of corresponding proxy services.