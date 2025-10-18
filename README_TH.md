# โปรแกรมอ่านบัตรประชาชนไทย (Thai ID Card Reader)

โปรแกรมนี้ใช้สำหรับอ่านข้อมูลจากบัตรประชาชนไทยด้วย Python และ smartcard reader

## ความต้องการของระบบ

### ฮาร์ดแวร์
- **Smartcard Reader** ที่รองรับบัตรประชาชนไทย เช่น:
  - SCR2700R
  - ACR38U
  - ACR39U
  - หรือ smartcard reader อื่นๆ ที่รองรับ PC/SC

### ซอฟต์แวร์
- Python 3.8 หรือใหม่กว่า
- macOS: ติดตั้ง PC/SC daemon (มักติดตั้งมาพร้อมระบบ)
- Windows: ติดตั้ง driver ของ smartcard reader
- Linux: ติดตั้ง `pcscd` package

## การติดตั้ง

### 1. Clone repository (ถ้ายังไม่ได้ทำ)
```bash
git clone https://github.com/preechai/python-smartcard-reader.git
cd python-smartcard-reader
```

### 2. สร้าง Virtual Environment
```bash
python3 -m venv env
source env/bin/activate  # บน macOS/Linux
# หรือ env\Scripts\activate บน Windows
```

### 3. ติดตั้ง dependencies
```bash
pip install -r requirements.txt
```

## การใช้งาน

### 1. เชื่อมต่อ smartcard reader กับคอมพิวเตอร์

### 2. ใส่บัตรประชาชนลงใน smartcard reader

### 3. รันโปรแกรม
```bash
python read.py
```

## ข้อมูลที่โปรแกรมสามารถอ่านได้

โปรแกรมจะแสดงข้อมูลดังนี้:
- **เลขบัตรประชาชน** (CID)
- **ชื่อ-นามสกุล** (ภาษาไทย)
- **ชื่อ-นามสกุล** (ภาษาอังกฤษ)
- **วันเกิด**
- **เพศ**
- **หน่วยงานออกบัตร**
- **วันออกบัตร**
- **วันหมดอายุ**
- **ที่อยู่**

### การแสดงรูปถ่าย
ในโค้ดมีส่วนการอ่านรูปถ่ายถูก comment ไว้ หากต้องการใช้งาน ให้เอา comment ออกในส่วน `# PHOTO` (บรรทัดที่ 101-124)

## ตัวอย่างผลลัพธ์

```
Available readers:
0 ACS ACR39U ICC Reader 00 00
Using: ACS ACR39U ICC Reader 00 00
ATR: 3B 67 00 00 00 00 00 00 00 00
Select Applet: 90 00
CID: 1234567890123
TH Fullname: นาย ทดสอบ ระบบ
EN Fullname: Mr. Test System
Date of birth: 01011990
Gender: 1
Card Issuer: กรมการปกครอง
Issue Date: 01012020
Expire Date: 01012025
Address: 123 ถนนทดสอบ แขวงทดสอบ เขททดสอบ กรุงเทพมหานคร 10100
```

## การแก้ปัญหา

### ไม่พบ smartcard reader
- ตรวจสอบว่าต่อสาย USB เรียบร้อยแล้ว
- ตรวจสอบว่าติดตั้ง driver แล้ว (Windows)
- รีบูตเครื่องหลังติดตั้ง driver

### Error: "No readers found"
- ตรวจสอบว่า PC/SC daemon ทำงานอยู่
  - macOS: `ps aux | grep pcscd`
  - Linux: `sudo systemctl status pcscd`
  - Windows: ตรวจสอบใน Services

### Error: "Card not inserted"
- ตรวจสอบว่าใส่บัตรถูกต้อง (ชิปหันเข้าหา reader)
- ลองเอาบัตรออกแล้วใส่ใหม่

## หมายเหตุ

- โปรแกรมนี้รองรับเฉพาะบัตรประชาชนไทยเท่านั้น
- ข้อมูลที่อ่านได้เป็นข้อมูลพื้นฐานที่เก็บอยู่ในชิปบัตร
- ไม่มีการเก็บหรือส่งข้อมูลไปที่ใดทั้งสิ้น ข้อมูลแสดงในเครื่องเท่านั้น

## License

ตามที่ระบุใน repository ต้นฉบับ

## เครดิต

- Original repository: https://github.com/preechai/python-smartcard-reader
- ผู้พัฒนา: preechai
