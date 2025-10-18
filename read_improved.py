#!/usr/bin/env python3
"""
โปรแกรมอ่านบัตรประชาชนไทยแบบปรับปรุง
Thai ID Card Reader - Improved Version
"""

import os
import sys
import json
import argparse
from datetime import datetime
from PIL import Image
import io

from smartcard.System import readers
from smartcard.util import HexListToBinString, toHexString

# ===== คำสั่ง APDU สำหรับอ่านข้อมูล =====
# Check card
SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08]
THAI_CARD = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]

# Commands
CMD_CID = [0x80, 0xb0, 0x00, 0x04, 0x02, 0x00, 0x0d]
CMD_THFULLNAME = [0x80, 0xb0, 0x00, 0x11, 0x02, 0x00, 0x64]
CMD_ENFULLNAME = [0x80, 0xb0, 0x00, 0x75, 0x02, 0x00, 0x64]
CMD_BIRTH = [0x80, 0xb0, 0x00, 0xD9, 0x02, 0x00, 0x08]
CMD_GENDER = [0x80, 0xb0, 0x00, 0xE1, 0x02, 0x00, 0x01]
CMD_ISSUER = [0x80, 0xb0, 0x00, 0xF6, 0x02, 0x00, 0x64]
CMD_ISSUE = [0x80, 0xb0, 0x01, 0x67, 0x02, 0x00, 0x08]
CMD_EXPIRE = [0x80, 0xb0, 0x01, 0x6F, 0x02, 0x00, 0x08]
CMD_ADDRESS = [0x80, 0xb0, 0x15, 0x79, 0x02, 0x00, 0x64]

# Photo commands
CMD_PHOTO = [
    [0x80, 0xb0, 0x01, 0x7B, 0x02, 0x00, 0xFF],  # Part 1
    [0x80, 0xb0, 0x02, 0x7A, 0x02, 0x00, 0xFF],  # Part 2
    [0x80, 0xb0, 0x03, 0x79, 0x02, 0x00, 0xFF],  # Part 3
    [0x80, 0xb0, 0x04, 0x78, 0x02, 0x00, 0xFF],  # Part 4
    [0x80, 0xb0, 0x05, 0x77, 0x02, 0x00, 0xFF],  # Part 5
    [0x80, 0xb0, 0x06, 0x76, 0x02, 0x00, 0xFF],  # Part 6
    [0x80, 0xb0, 0x07, 0x75, 0x02, 0x00, 0xFF],  # Part 7
    [0x80, 0xb0, 0x08, 0x74, 0x02, 0x00, 0xFF],  # Part 8
    [0x80, 0xb0, 0x09, 0x73, 0x02, 0x00, 0xFF],  # Part 9
    [0x80, 0xb0, 0x0A, 0x72, 0x02, 0x00, 0xFF],  # Part 10
    [0x80, 0xb0, 0x0B, 0x71, 0x02, 0x00, 0xFF],  # Part 11
    [0x80, 0xb0, 0x0C, 0x70, 0x02, 0x00, 0xFF],  # Part 12
    [0x80, 0xb0, 0x0D, 0x6F, 0x02, 0x00, 0xFF],  # Part 13
    [0x80, 0xb0, 0x0E, 0x6E, 0x02, 0x00, 0xFF],  # Part 14
    [0x80, 0xb0, 0x0F, 0x6D, 0x02, 0x00, 0xFF],  # Part 15
    [0x80, 0xb0, 0x10, 0x6C, 0x02, 0x00, 0xFF],  # Part 16
    [0x80, 0xb0, 0x11, 0x6B, 0x02, 0x00, 0xFF],  # Part 17
    [0x80, 0xb0, 0x12, 0x6A, 0x02, 0x00, 0xFF],  # Part 18
    [0x80, 0xb0, 0x13, 0x69, 0x02, 0x00, 0xFF],  # Part 19
    [0x80, 0xb0, 0x14, 0x68, 0x02, 0x00, 0xFF],  # Part 20
]


def thai2unicode(data):
    """แปลง bytes เป็น unicode โดยใช้ encoding TIS-620"""
    try:
        result = bytes(data).decode('tis-620')
        return result.strip()
    except Exception as e:
        print(f"Error decoding: {e}")
        return ""


def get_data(connection, cmd, req=[0x00, 0xc0, 0x00, 0x00]):
    """ส่งคำสั่งไปยังบัตรและรับข้อมูลกลับ"""
    try:
        data, sw1, sw2 = connection.transmit(cmd)
        data, sw1, sw2 = connection.transmit(req + [cmd[-1]])
        return data, sw1, sw2
    except Exception as e:
        print(f"Error getting data: {e}")
        return [], 0x00, 0x00


def format_date(date_str):
    """จัดรูปแบบวันที่จาก DDMMYYYY เป็น DD/MM/YYYY"""
    if len(date_str) == 8:
        return f"{date_str[0:2]}/{date_str[2:4]}/{date_str[4:8]}"
    return date_str


def read_thai_id_card(connection, atr, save_photo=False, output_dir="output"):
    """อ่านข้อมูลจากบัตรประชาชนไทย"""
    
    # กำหนด request code ตาม ATR
    if atr[0] == 0x3B and atr[1] == 0x67:
        req = [0x00, 0xc0, 0x00, 0x01]
    else:
        req = [0x00, 0xc0, 0x00, 0x00]
    
    # ตรวจสอบว่าเป็นบัตรไทยหรือไม่
    data, sw1, sw2 = connection.transmit(SELECT + THAI_CARD)
    print(f"Select Applet: {sw1:02X} {sw2:02X}")
    
    if sw1 != 0x90 or sw2 != 0x00:
        print("ไม่พบบัตรประชาชนไทย!")
        return None
    
    # สร้าง dictionary เก็บข้อมูล
    card_data = {}
    
    # อ่านข้อมูลแต่ละส่วน
    print("\n" + "="*50)
    print("ข้อมูลจากบัตรประชาชน")
    print("="*50)
    
    # CID
    data, sw1, sw2 = get_data(connection, CMD_CID, req)
    cid = thai2unicode(data)
    card_data['cid'] = cid
    print(f"เลขบัตรประชาชน: {cid}")
    
    # Thai Fullname
    data, sw1, sw2 = get_data(connection, CMD_THFULLNAME, req)
    th_name = thai2unicode(data)
    card_data['th_fullname'] = th_name
    print(f"ชื่อ-นามสกุล (ไทย): {th_name}")
    
    # English Fullname
    data, sw1, sw2 = get_data(connection, CMD_ENFULLNAME, req)
    en_name = thai2unicode(data)
    card_data['en_fullname'] = en_name
    print(f"ชื่อ-นามสกุล (อังกฤษ): {en_name}")
    
    # Date of birth
    data, sw1, sw2 = get_data(connection, CMD_BIRTH, req)
    birth = thai2unicode(data)
    card_data['birth_date'] = format_date(birth)
    print(f"วันเกิด: {format_date(birth)}")
    
    # Gender
    data, sw1, sw2 = get_data(connection, CMD_GENDER, req)
    gender = thai2unicode(data)
    gender_text = "ชาย" if gender == "1" else "หญิง"
    card_data['gender'] = gender_text
    print(f"เพศ: {gender_text}")
    
    # Card Issuer
    data, sw1, sw2 = get_data(connection, CMD_ISSUER, req)
    issuer = thai2unicode(data)
    card_data['issuer'] = issuer
    print(f"หน่วยงานออกบัตร: {issuer}")
    
    # Issue Date
    data, sw1, sw2 = get_data(connection, CMD_ISSUE, req)
    issue = thai2unicode(data)
    card_data['issue_date'] = format_date(issue)
    print(f"วันออกบัตร: {format_date(issue)}")
    
    # Expire Date
    data, sw1, sw2 = get_data(connection, CMD_EXPIRE, req)
    expire = thai2unicode(data)
    card_data['expire_date'] = format_date(expire)
    print(f"วันหมดอายุ: {format_date(expire)}")
    
    # Address
    data, sw1, sw2 = get_data(connection, CMD_ADDRESS, req)
    address = thai2unicode(data)
    card_data['address'] = address
    print(f"ที่อยู่: {address}")
    
    print("="*50 + "\n")
    
    # อ่านรูปถ่าย (ถ้าต้องการ)
    if save_photo:
        print("กำลังอ่านรูปถ่าย...")
        photo_data = []
        for i, cmd in enumerate(CMD_PHOTO, 1):
            data, sw1, sw2 = get_data(connection, cmd, req)
            photo_data.extend(data)
            print(f"  อ่านส่วนที่ {i}/20")
        
        # บันทึกรูปถ่าย
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        photo_filename = f"{output_dir}/{cid}.jpg"
        photo_bytes = HexListToBinString(photo_data)
        
        with open(photo_filename, "wb") as f:
            f.write(photo_bytes)
        
        print(f"บันทึกรูปถ่ายที่: {photo_filename}\n")
        card_data['photo_path'] = photo_filename
    
    # เพิ่มข้อมูล timestamp
    card_data['read_timestamp'] = datetime.now().isoformat()
    
    return card_data


def save_to_json(data, output_dir="output"):
    """บันทึกข้อมูลเป็น JSON file"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{output_dir}/{data['cid']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"บันทึกข้อมูลที่: {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(
        description='โปรแกรมอ่านบัตรประชาชนไทย',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ตัวอย่างการใช้งาน:
  python read_improved.py                    # อ่านข้อมูลเบื้องต้น
  python read_improved.py --photo           # อ่านพร้อมบันทึกรูปถ่าย
  python read_improved.py --json            # บันทึกเป็น JSON
  python read_improved.py --photo --json    # อ่านทั้งหมดและบันทึก
        """
    )
    
    parser.add_argument('--photo', action='store_true',
                       help='บันทึกรูปถ่ายจากบัตร')
    parser.add_argument('--json', action='store_true',
                       help='บันทึกข้อมูลเป็น JSON file')
    parser.add_argument('--output-dir', default='output',
                       help='โฟลเดอร์สำหรับบันทึกไฟล์ (default: output)')
    parser.add_argument('--reader', type=int, default=0,
                       help='เลือก reader (default: 0)')
    
    args = parser.parse_args()
    
    try:
        # แสดง readers ที่มี
        reader_list = readers()
        
        if not reader_list:
            print("ไม่พบ smartcard reader!")
            print("กรุณาตรวจสอบว่าเชื่อมต่อ reader แล้ว")
            return 1
        
        print("Smartcard Readers ที่พบ:")
        for idx, r in enumerate(reader_list):
            print(f"  [{idx}] {r}")
        
        # เลือก reader
        if args.reader >= len(reader_list):
            print(f"\nError: Reader index {args.reader} ไม่มีอยู่")
            return 1
        
        reader = reader_list[args.reader]
        print(f"\nใช้งาน: {reader}")
        
        # เชื่อมต่อกับบัตร
        connection = reader.createConnection()
        connection.connect()
        
        atr = connection.getATR()
        print(f"ATR: {toHexString(atr)}\n")
        
        # อ่านข้อมูลจากบัตร
        card_data = read_thai_id_card(
            connection, 
            atr, 
            save_photo=args.photo,
            output_dir=args.output_dir
        )
        
        if card_data is None:
            return 1
        
        # บันทึกเป็น JSON (ถ้าต้องการ)
        if args.json:
            save_to_json(card_data, args.output_dir)
        
        print("อ่านข้อมูลสำเร็จ!")
        return 0
        
    except Exception as e:
        print(f"\nเกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
