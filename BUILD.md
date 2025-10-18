# คู่มือการ Build โปรแกรมอ่านบัตรประชาชนไทย

คู่มือนี้จะแนะนำวิธีการ build โปรแกรมเป็น executable file สำหรับ Windows (.exe) และ macOS (.app/.dmg)

## 📋 ข้อกำหนดเบื้องต้น

### สำหรับทุกแพลตฟอร์ม
- Python 3.8 หรือสูงกว่า
- Smart Card Reader (ตัวอ่านบัตร)
- PC/SC Lite drivers (สำหรับ macOS)

### สำหรับ Windows
- Python 3.8+ (ดาวน์โหลดจาก [python.org](https://www.python.org/downloads/))
- Microsoft Visual C++ Redistributable (มักจะมีติดมากับ Windows แล้ว)

### สำหรับ macOS
- Python 3.8+ (ติดตั้งผ่าน Homebrew: `brew install python3`)
- Xcode Command Line Tools: `xcode-select --install`
- Homebrew (สำหรับติดตั้ง create-dmg): [brew.sh](https://brew.sh)

## 🔨 วิธีการ Build

### สำหรับ macOS

1. **เปิด Terminal และไปที่โฟลเดอร์โปรเจค**
   ```bash
   cd /path/to/id_scan
   ```

2. **รัน build script**
   ```bash
   ./build_mac.sh
   ```

3. **รอให้ build เสร็จสิ้น**
   - Script จะสร้าง virtual environment อัตโนมัติ
   - ติดตั้ง dependencies ที่จำเป็น
   - Build application ด้วย PyInstaller
   - ผลลัพธ์: `dist/ThaiIDCardReader.app`

4. **สร้าง DMG installer (ไม่บังคับ)**
   ```bash
   ./create_dmg_mac.sh
   ```
   - ผลลัพธ์: `dist/ThaiIDCardReader.dmg`
   - ใช้ไฟล์นี้ในการแจกจ่ายโปรแกรม

5. **ทดสอบโปรแกรม**
   ```bash
   open dist/ThaiIDCardReader.app
   ```

### สำหรับ Windows

1. **เปิด Command Prompt หรือ PowerShell และไปที่โฟลเดอร์โปรเจค**
   ```cmd
   cd C:\path\to\id_scan
   ```

2. **รัน build script**
   ```cmd
   build_windows.bat
   ```

3. **รอให้ build เสร็จสิ้น**
   - Script จะสร้าง virtual environment อัตโนมัติ
   - ติดตั้ง dependencies ที่จำเป็น
   - Build application ด้วย PyInstaller
   - ผลลัพธ์: `dist\ThaiIDCardReader.exe`

4. **ทดสอบโปรแกรม**
   ```cmd
   dist\ThaiIDCardReader.exe
   ```

## 📦 โครงสร้างไฟล์ที่สร้างขึ้น

```
id_scan/
├── dist/                          # โฟลเดอร์ output
│   ├── ThaiIDCardReader.exe       # Windows executable
│   ├── ThaiIDCardReader.app       # macOS application
│   └── ThaiIDCardReader.dmg       # macOS installer (ถ้าสร้าง)
├── build/                         # ไฟล์ชั่วคราวจาก PyInstaller
├── venv/                          # Virtual environment (ไม่ commit)
├── gui_reader.py                  # Source code หลัก
├── build_requirements.txt         # Dependencies สำหรับ build
├── id_card_reader.spec           # PyInstaller configuration
├── build_mac.sh                   # Build script สำหรับ Mac
├── build_windows.bat              # Build script สำหรับ Windows
└── create_dmg_mac.sh             # สร้าง DMG installer สำหรับ Mac
```

## ⚙️ การตั้งค่าเพิ่มเติม

### เพิ่ม Icon ให้โปรแกรม

1. เตรียมไฟล์ icon:
   - Windows: `icon.ico` (ขนาดแนะนำ 256x256)
   - macOS: `icon.icns` (ขนาดแนะนำ 512x512)

2. แก้ไขไฟล์ `id_card_reader.spec`:
   ```python
   # หาบรรทัด icon=None และแก้เป็น
   icon='path/to/icon.ico'  # สำหรับ Windows
   # หรือ
   icon='path/to/icon.icns'  # สำหรับ Mac
   ```

### ปรับแต่งข้อมูลโปรแกรม

แก้ไขใน `id_card_reader.spec`:
- `CFBundleName`: ชื่อโปรแกรม
- `CFBundleVersion`: เวอร์ชัน
- `NSHumanReadableCopyright`: ข้อมูล Copyright

## 🐛 การแก้ปัญหา

### macOS: "ThaiIDCardReader.app is damaged and can't be opened"

วิธีแก้:
```bash
xattr -cr dist/ThaiIDCardReader.app
```

### Windows: "Python is not recognized"

วิธีแก้:
1. ตรวจสอบว่าติดตั้ง Python แล้ว
2. เพิ่ม Python เข้า PATH:
   - Control Panel → System → Advanced → Environment Variables
   - เพิ่ม path ของ Python (เช่น `C:\Python39`)

### การ Build ล้มเหลว

วิธีแก้:
1. ลบ `build/` และ `dist/` folders
   ```bash
   # Mac/Linux
   rm -rf build dist
   
   # Windows
   rmdir /s build dist
   ```

2. ลบ virtual environment และสร้างใหม่
   ```bash
   # Mac/Linux
   rm -rf venv
   
   # Windows
   rmdir /s venv
   ```

3. รัน build script อีกครั้ง

### Smart Card Reader ไม่ทำงาน

**สำหรับ macOS:**
- ตรวจสอบว่าติดตั้ง PC/SC drivers แล้ว
- ลอง restart บริการ: `sudo killall pcscd`

**สำหรับ Windows:**
- ตรวจสอบใน Device Manager ว่า reader ถูกติดตั้งอย่างถูกต้อง
- ติดตั้ง driver จากผู้ผลิต reader

## 📝 หมายเหตุ

1. ไฟล์ที่ build ออกมาจะมีขนาดใหญ่กว่า source code เดิม เนื่องจากมี Python runtime และ libraries ทั้งหมดรวมอยู่

2. สำหรับการแจกจ่าย:
   - **Windows**: แจกจ่ายไฟล์ `.exe` โดยตรง
   - **macOS**: แนะนำให้สร้าง `.dmg` เพื่อความสะดวกในการติดตั้ง

3. การทดสอบ:
   - ทดสอบบนเครื่องที่ไม่มี Python ติดตั้ง เพื่อให้แน่ใจว่าโปรแกรมทำงานได้อย่างเป็นอิสระ
   - ทดสอบกับ Smart Card Reader หลายรุ่น

## 🔐 Code Signing (สำหรับการแจกจ่ายจริง)

### macOS
```bash
# ต้องมี Apple Developer Account
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/ThaiIDCardReader.app
```

### Windows
- ใช้ Certificate จาก Certificate Authority
- ใช้ SignTool จาก Windows SDK

## 📞 การขอความช่วยเหลือ

หากพบปัญหาในการ build สามารถ:
1. ตรวจสอบ error message ใน terminal/command prompt
2. ตรวจสอบไฟล์ log ใน `build/` folder
3. ลองลบ cache และ build ใหม่
4. ตรวจสอบว่า dependencies ทั้งหมดติดตั้งครบถ้วน

---

## 📊 เวอร์ชัน

- เวอร์ชัน: 1.0.0
- อัพเดทล่าสุด: 2025
- ใช้ PyInstaller 6.0.0+
