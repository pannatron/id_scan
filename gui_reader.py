#!/usr/bin/env python3
"""
โปรแกรมอ่านบัตรประชาชนไทยแบบ GUI
Thai ID Card Reader with GUI
"""

import os
import sys
import csv
import threading
import time
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException

# Import functions from read_improved
from smartcard.util import HexListToBinString

# Constants
SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08]
THAI_CARD = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]
CMD_CID = [0x80, 0xb0, 0x00, 0x04, 0x02, 0x00, 0x0d]
CMD_THFULLNAME = [0x80, 0xb0, 0x00, 0x11, 0x02, 0x00, 0x64]
CMD_ENFULLNAME = [0x80, 0xb0, 0x00, 0x75, 0x02, 0x00, 0x64]
CMD_BIRTH = [0x80, 0xb0, 0x00, 0xD9, 0x02, 0x00, 0x08]
CMD_GENDER = [0x80, 0xb0, 0x00, 0xE1, 0x02, 0x00, 0x01]
CMD_ISSUER = [0x80, 0xb0, 0x00, 0xF6, 0x02, 0x00, 0x64]
CMD_ISSUE = [0x80, 0xb0, 0x01, 0x67, 0x02, 0x00, 0x08]
CMD_EXPIRE = [0x80, 0xb0, 0x01, 0x6F, 0x02, 0x00, 0x08]
CMD_ADDRESS = [0x80, 0xb0, 0x15, 0x79, 0x02, 0x00, 0x64]


def thai2unicode(data):
    """แปลง bytes เป็น unicode โดยใช้ encoding TIS-620"""
    try:
        result = bytes(data).decode('tis-620')
        return result.strip()
    except:
        return ""


def get_data(connection, cmd, req=[0x00, 0xc0, 0x00, 0x00]):
    """ส่งคำสั่งไปยังบัตรและรับข้อมูลกลับ"""
    try:
        data, sw1, sw2 = connection.transmit(cmd)
        data, sw1, sw2 = connection.transmit(req + [cmd[-1]])
        return data, sw1, sw2
    except:
        return [], 0x00, 0x00


def format_date(date_str):
    """จัดรูปแบบวันที่จาก YYYYMMDD เป็น DD/MM/YYYY"""
    if len(date_str) == 8:
        year = date_str[0:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{day}/{month}/{year}"
    return date_str


def parse_name(fullname):
    """แยกชื่อจากรูปแบบ คำนำหน้า#ชื่อ##นามสกุล"""
    try:
        # แยกด้วย ## ก่อนเพื่อแยกนามสกุล
        parts = fullname.split('##')
        if len(parts) == 2:
            name_part = parts[0]  # คำนำหน้า#ชื่อ
            lastname = parts[1].strip()
            
            # แยกคำนำหน้าและชื่อด้วย #
            name_parts = name_part.split('#')
            if len(name_parts) >= 2:
                title = name_parts[0].strip()
                firstname = name_parts[1].strip()
                return {
                    'title': title,
                    'firstname': firstname,
                    'lastname': lastname,
                    'fullname': f"{title} {firstname} {lastname}"
                }
        
        # ถ้าไม่สามารถแยกได้ ให้คืนค่าเดิม
        return {
            'title': '',
            'firstname': '',
            'lastname': '',
            'fullname': fullname.replace('#', ' ')
        }
    except:
        return {
            'title': '',
            'firstname': '',
            'lastname': '',
            'fullname': fullname
        }


def parse_address(address):
    """แยกที่อยู่จากรูปแบบ บ้านเลขที่###หมู่/ซอย##ตำบล#อำเภอ#จังหวัด"""
    try:
        import re
        
        # Debug: แสดงข้อมูลดิบ
        print(f"Raw address: {repr(address)}")
        
        # ทำความสะอาดข้อมูล - ลบตัวเลข 4 หลักที่อาจเป็นปีพ.ศ. ที่อยู่ข้างหน้า
        address = re.sub(r'^\d{4}\s+', '', address)
        
        house_no = ''
        moo_soi = ''
        subdistrict = ''
        district = ''
        province = ''
        
        # แยกข้อมูลตาม delimiter
        if '###' in address:
            # กรณีมี ### แยกบ้านเลขที่ออก
            parts = address.split('###', 1)
            house_no = parts[0].strip()
            rest = parts[1] if len(parts) > 1 else ''
            
            # แยก rest ด้วย ## ถ้ามี
            if '##' in rest:
                moo_soi_part, rest = rest.split('##', 1)
                moo_soi = moo_soi_part.strip()
            else:
                # ไม่มี ## ต้องหาว่า moo/soi อยู่ไหน จบที่ไหน
                # หาคำที่บ่งบอกตำบล เช่น "แขวง", "ตำบล"
                match = re.search(r'\s+(แขวง|ตำบล)', rest)
                if match:
                    split_pos = match.start()
                    moo_soi = rest[:split_pos].strip()
                    rest = rest[split_pos:].strip()
                elif '#' in rest:
                    parts_temp = rest.split('#', 1)
                    moo_soi = parts_temp[0].strip()
                    rest = parts_temp[1] if len(parts_temp) > 1 else ''
                else:
                    moo_soi = rest.strip()
                    rest = ''
        else:
            # กรณีไม่มี ### ให้แยกด้วย ## ก่อน
            if '##' in address:
                parts = address.split('##', 1)
                first_part = parts[0]
                rest = parts[1] if len(parts) > 1 else ''
                
                # แยก first_part ด้วย #
                if '#' in first_part:
                    sub_parts = first_part.split('#', 1)
                    house_no = sub_parts[0].strip()
                    moo_soi = sub_parts[1].strip() if len(sub_parts) > 1 else ''
                else:
                    house_no = first_part.strip()
            else:
                # ไม่มีทั้ง ### และ ## ให้แยกด้วย #
                if '#' in address:
                    all_parts = address.split('#')
                    if len(all_parts) >= 1:
                        house_no = all_parts[0].strip()
                    if len(all_parts) >= 2:
                        moo_soi = all_parts[1].strip()
                    if len(all_parts) >= 3:
                        subdistrict = all_parts[2].strip()
                    if len(all_parts) >= 4:
                        district = all_parts[3].strip()
                    if len(all_parts) >= 5:
                        province = all_parts[4].strip()
                else:
                    rest = address
        
        # แยกส่วนที่เหลือ (ตำบล#อำเภอ#จังหวัด)
        if rest:
            rest = rest.replace('##', '#')
            address_parts = [p.strip() for p in rest.split('#') if p.strip()]
            
            print(f"Remaining parts: {address_parts}")
            
            # กำหนดค่าตามลำดับ
            if len(address_parts) >= 1:
                subdistrict = address_parts[0]
            if len(address_parts) >= 2:
                district = address_parts[1]
            if len(address_parts) >= 3:
                province = address_parts[2]
        
        # Post-processing: อนุมานและแก้ไขข้อมูลที่ผิด
        # 1. ถ้า moo_soi มีคำว่า "แขวง" หรือ "ตำบล" และ subdistrict ว่าง
        if moo_soi and not subdistrict:
            match = re.search(r'(แขวง|ตำบล)', moo_soi)
            if match:
                # แยก moo_soi ออกเป็นสองส่วน
                split_pos = match.start()
                actual_moo_soi = moo_soi[:split_pos].strip()
                actual_subdistrict = moo_soi[split_pos:].strip()
                
                # ถ้า subdistrict ว่าง ให้เลื่อนค่า
                if not subdistrict and district:
                    province = district
                    district = subdistrict
                    subdistrict = actual_subdistrict
                    moo_soi = actual_moo_soi
                elif not subdistrict:
                    subdistrict = actual_subdistrict
                    moo_soi = actual_moo_soi
        
        # 2. ถ้า house_no มี # อยู่ ให้แยกออก
        if '#' in house_no:
            parts = house_no.split('#', 1)
            house_no = parts[0].strip()
            if not moo_soi and len(parts) > 1:
                moo_soi = parts[1].strip()
        
        # ลบ # ออกจากทุกฟิลด์
        house_no = house_no.replace('#', '').strip()
        moo_soi = moo_soi.replace('#', '').strip()
        subdistrict = subdistrict.replace('#', '').strip()
        district = district.replace('#', '').strip()
        province = province.replace('#', '').strip()
        
        # Debug output
        print(f"Final: house={house_no}, moo={moo_soi}, sub={subdistrict}, dist={district}, prov={province}")
        
        # สร้างที่อยู่แบบเต็ม
        full_parts = []
        if house_no:
            full_parts.append(house_no)
        if moo_soi:
            full_parts.append(moo_soi)
        if subdistrict:
            full_parts.append(subdistrict)
        if district:
            full_parts.append(district)
        if province:
            full_parts.append(province)
        
        fulladdress = ' '.join(full_parts)
        
        return {
            'house_no': house_no,
            'moo_soi': moo_soi,
            'subdistrict': subdistrict,
            'district': district,
            'province': province,
            'fulladdress': fulladdress
        }
    except Exception as e:
        print(f"Error parsing address: {e}")
        import traceback
        traceback.print_exc()
        return {
            'house_no': '',
            'moo_soi': '',
            'subdistrict': '',
            'district': '',
            'province': '',
            'fulladdress': address.replace('#', ' ')
        }


class IDCardReaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("โปรแกรมอ่านบัตรประชาชนไทย")
        self.root.geometry("1200x700")
        
        # Data storage
        self.card_data_list = []
        self.current_cid = None
        self.monitoring = False
        self.reader = None
        self.connection = None
        
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        """สร้าง UI"""
        
        # Top Frame - Project Info
        top_frame = ttk.LabelFrame(self.root, text="ข้อมูลโครงการ", padding=10)
        top_frame.pack(fill=X, padx=10, pady=5)
        
        # Project Name
        ttk.Label(top_frame, text="ชื่อโครงการ:").grid(row=0, column=0, sticky=W, padx=5)
        self.project_name = StringVar()
        ttk.Entry(top_frame, textvariable=self.project_name, width=40).grid(row=0, column=1, padx=5)
        
        # School Name
        ttk.Label(top_frame, text="ชื่อโรงเรียน:").grid(row=0, column=2, sticky=W, padx=5)
        self.school_name = StringVar()
        ttk.Entry(top_frame, textvariable=self.school_name, width=40).grid(row=0, column=3, padx=5)
        
        # Status Frame
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=X, padx=10, pady=5)
        
        # Reader Status
        ttk.Label(status_frame, text="สถานะ Reader:").pack(side=LEFT, padx=5)
        self.reader_status = StringVar(value="กำลังค้นหา...")
        self.reader_status_label = ttk.Label(status_frame, textvariable=self.reader_status, foreground="orange")
        self.reader_status_label.pack(side=LEFT, padx=5)
        
        # Card Status
        ttk.Label(status_frame, text="สถานะบัตร:").pack(side=LEFT, padx=20)
        self.card_status = StringVar(value="รอเสียบบัตร")
        self.card_status_label = ttk.Label(status_frame, textvariable=self.card_status, foreground="gray")
        self.card_status_label.pack(side=LEFT, padx=5)
        
        # Data count
        ttk.Label(status_frame, text="จำนวนข้อมูล:").pack(side=LEFT, padx=20)
        self.data_count = StringVar(value="0 คน")
        ttk.Label(status_frame, textvariable=self.data_count, foreground="blue").pack(side=LEFT, padx=5)
        
        # Table Frame
        table_frame = ttk.LabelFrame(self.root, text="ข้อมูลที่อ่านได้", padding=10)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview
        columns = ("ลำดับ", "เลขบัตร", "ชื่อ-นามสกุล (ไทย)", "ชื่อ-นามสกุล (อังกฤษ)", 
                   "วันเกิด", "เพศ", "วันที่อ่าน")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Column headings
        col_widths = [50, 130, 200, 200, 90, 60, 150]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=CENTER if col in ["ลำดับ", "เพศ"] else W)
        
        # Pack scrollbars and tree
        vsb.pack(side=RIGHT, fill=Y)
        hsb.pack(side=BOTTOM, fill=X)
        self.tree.pack(fill=BOTH, expand=True)
        
        # Bottom Frame - Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=X, padx=10, pady=10)
        
        # Import Button
        ttk.Button(button_frame, text="📥 Import จาก CSV", 
                  command=self.import_from_csv, width=20).pack(side=LEFT, padx=5)
        
        # Export Button
        self.export_btn = ttk.Button(button_frame, text="📄 Export เป็น CSV", 
                                     command=self.export_to_csv, width=20)
        self.export_btn.pack(side=LEFT, padx=5)
        
        # Clear Button
        ttk.Button(button_frame, text="🗑️ ลบข้อมูลทั้งหมด", 
                  command=self.clear_all_data, width=20).pack(side=LEFT, padx=5)
        
        # Refresh Button
        ttk.Button(button_frame, text="🔄 รีเฟรช Reader", 
                  command=self.refresh_reader, width=20).pack(side=LEFT, padx=5)
        
        # View Details Button
        ttk.Button(button_frame, text="👁️ ดูรายละเอียด", 
                  command=self.view_details, width=20).pack(side=LEFT, padx=5)
        
        # Exit Button
        ttk.Button(button_frame, text="❌ ออก", 
                  command=self.on_closing, width=15).pack(side=RIGHT, padx=5)
        
    def find_reader(self):
        """ค้นหา smartcard reader"""
        try:
            reader_list = readers()
            if reader_list:
                self.reader = reader_list[0]
                self.reader_status.set(f"✓ {self.reader}")
                self.root.after(0, lambda: self.reader_status_label.config(foreground="green"))
                # เพิ่ม delay เล็กน้อยให้ reader พร้อมใช้งาน
                time.sleep(0.5)
                return True
            else:
                self.reader_status.set("✗ ไม่พบ Reader")
                self.root.after(0, lambda: self.reader_status_label.config(foreground="red"))
                return False
        except Exception as e:
            self.reader_status.set(f"✗ Error: {str(e)}")
            self.root.after(0, lambda: self.reader_status_label.config(foreground="red"))
            return False
    
    def start_monitoring(self):
        """เริ่ม monitoring บัตร"""
        self.monitoring = True
        thread = threading.Thread(target=self.monitor_card, daemon=True)
        thread.start()
    
    def monitor_card(self):
        """ตรวจสอบการเสียบ/ถอดบัตรอย่างต่อเนื่อง"""
        while self.monitoring:
            try:
                # ค้นหา reader ถ้ายังไม่มี
                if not self.reader:
                    self.find_reader()
                    time.sleep(2)
                    continue
                
                # ลองเชื่อมต่อกับบัตร
                try:
                    connection = self.reader.createConnection()
                    connection.connect()
                    
                    # เพิ่ม delay หลัง connect เพื่อให้การ์ดพร้อม
                    time.sleep(0.3)
                    
                    # อ่าน ATR
                    atr = connection.getATR()
                    print(f"ATR detected: {toHexString(atr)}")  # Debug
                    
                    # กำหนด request code ตาม ATR
                    if atr[0] == 0x3B and atr[1] == 0x67:
                        req = [0x00, 0xc0, 0x00, 0x01]
                    else:
                        req = [0x00, 0xc0, 0x00, 0x00]
                    
                    # ตรวจสอบว่าเป็นบัตรไทย (retry ถ้าล้มเหลว)
                    max_retries = 3
                    sw1, sw2 = 0x00, 0x00
                    
                    for retry in range(max_retries):
                        try:
                            data, sw1, sw2 = connection.transmit(SELECT + THAI_CARD)
                            print(f"Select applet response (attempt {retry+1}): {sw1:02X} {sw2:02X}")
                            
                            # 0x90 = success, 0x61 = success with data available
                            if sw1 == 0x90 or sw1 == 0x61:
                                break
                            
                            # ถ้าไม่สำเร็จ รอแล้วลองใหม่
                            if retry < max_retries - 1:
                                time.sleep(0.2)
                        except Exception as e:
                            print(f"Retry {retry+1} failed: {e}")
                            if retry < max_retries - 1:
                                time.sleep(0.2)
                    
                    if sw1 == 0x90 or sw1 == 0x61:
                        # อ่านเลขบัตร
                        data, sw1, sw2 = get_data(connection, CMD_CID, req)
                        cid = thai2unicode(data)
                        print(f"CID: {cid}")  # Debug
                        
                        # ถ้าเป็นบัตรใหม่ ให้อ่านข้อมูล
                        if cid and cid != self.current_cid:
                            self.current_cid = cid
                            self.update_card_status("🔄 กำลังอ่านข้อมูล...", "orange")
                            
                            # อ่านข้อมูลทั้งหมด
                            card_info = self.read_card_data(connection, req, cid)
                            
                            if card_info:
                                # เพิ่มข้อมูลลงในตาราง
                                self.root.after(0, lambda ci=card_info: self.add_card_to_table(ci))
                                self.update_card_status("✓ อ่านสำเร็จ - รอถอดบัตร", "green")
                        elif cid:
                            self.update_card_status("⏸️ บัตรใบเดิม - รอถอดบัตร", "blue")
                    
                except NoCardException:
                    # ไม่มีบัตร - รีเซ็ตสถานะ
                    if self.current_cid:
                        self.current_cid = None
                        self.update_card_status("⏳ รอเสียบบัตรใหม่", "gray")
                    
                except CardConnectionException as e:
                    print(f"Card connection error: {e}")
                
            except Exception as e:
                print(f"Monitor error: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(0.5)  # ตรวจสอบทุก 0.5 วินาที
    
    def update_card_status(self, status_text, color):
        """อัพเดทสถานะบัตรอย่างปลอดภัยจาก thread"""
        def update():
            self.card_status.set(status_text)
            self.card_status_label.config(foreground=color)
        self.root.after(0, update)
    
    def read_card_data(self, connection, req, cid):
        """อ่านข้อมูลจากบัตร"""
        try:
            card_info = {
                'cid': cid,
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            
            # Thai Fullname
            data, sw1, sw2 = get_data(connection, CMD_THFULLNAME, req)
            th_name_raw = thai2unicode(data)
            th_name_parsed = parse_name(th_name_raw)
            card_info['th_title'] = th_name_parsed['title']
            card_info['th_firstname'] = th_name_parsed['firstname']
            card_info['th_lastname'] = th_name_parsed['lastname']
            card_info['th_fullname'] = th_name_parsed['fullname']
            
            # English Fullname
            data, sw1, sw2 = get_data(connection, CMD_ENFULLNAME, req)
            en_name_raw = thai2unicode(data)
            en_name_parsed = parse_name(en_name_raw)
            card_info['en_title'] = en_name_parsed['title']
            card_info['en_firstname'] = en_name_parsed['firstname']
            card_info['en_lastname'] = en_name_parsed['lastname']
            card_info['en_fullname'] = en_name_parsed['fullname']
            
            # Date of birth
            data, sw1, sw2 = get_data(connection, CMD_BIRTH, req)
            card_info['birth_date'] = format_date(thai2unicode(data))
            
            # Gender
            data, sw1, sw2 = get_data(connection, CMD_GENDER, req)
            gender = thai2unicode(data)
            card_info['gender'] = "ชาย" if gender == "1" else "หญิง"
            
            # Card Issuer
            data, sw1, sw2 = get_data(connection, CMD_ISSUER, req)
            card_info['issuer'] = thai2unicode(data)
            
            # Issue Date
            data, sw1, sw2 = get_data(connection, CMD_ISSUE, req)
            card_info['issue_date'] = format_date(thai2unicode(data))
            
            # Expire Date
            data, sw1, sw2 = get_data(connection, CMD_EXPIRE, req)
            card_info['expire_date'] = format_date(thai2unicode(data))
            
            # Address
            data, sw1, sw2 = get_data(connection, CMD_ADDRESS, req)
            address_raw = thai2unicode(data)
            address_parsed = parse_address(address_raw)
            card_info['address_house_no'] = address_parsed['house_no']
            card_info['address_moo_soi'] = address_parsed['moo_soi']
            card_info['address_subdistrict'] = address_parsed['subdistrict']
            card_info['address_district'] = address_parsed['district']
            card_info['address_province'] = address_parsed['province']
            card_info['address'] = address_parsed['fulladdress']
            
            return card_info
            
        except Exception as e:
            print(f"Error reading card: {e}")
            return None
    
    def add_card_to_table(self, card_info):
        """เพิ่มข้อมูลลงในตาราง"""
        # ตรวจสอบว่ามีข้อมูลซ้ำหรือไม่
        for data in self.card_data_list:
            if data['cid'] == card_info['cid']:
                messagebox.showwarning("ข้อมูลซ้ำ", 
                    f"เลขบัตร {card_info['cid']} มีในระบบแล้ว")
                return
        
        # เพิ่มข้อมูล
        self.card_data_list.append(card_info)
        
        # แสดงในตาราง
        index = len(self.card_data_list)
        self.tree.insert("", END, values=(
            index,
            card_info['cid'],
            card_info['th_fullname'],
            card_info['en_fullname'],
            card_info['birth_date'],
            card_info['gender'],
            card_info['timestamp']
        ))
        
        # อัพเดทจำนวน
        self.data_count.set(f"{len(self.card_data_list)} คน")
        
        # Scroll to bottom
        self.tree.see(self.tree.get_children()[-1])
    
    def import_from_csv(self):
        """Import ข้อมูลจาก CSV"""
        # เลือกไฟล์
        filename = filedialog.askopenfilename(
            title="เลือกไฟล์ CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            imported_count = 0
            duplicate_count = 0
            error_count = 0
            
            with open(filename, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # ตรวจสอบว่าเป็นไฟล์ที่ export จากโปรแกรมนี้หรือไม่
                required_fields = ['เลขบัตรประชาชน', 'ชื่อ (ไทย)', 'นามสกุล (ไทย)']
                if not all(field in reader.fieldnames for field in required_fields):
                    messagebox.showerror("รูปแบบไฟล์ไม่ถูกต้อง", 
                        "ไฟล์ CSV นี้ไม่ใช่ไฟล์ที่ export จากโปรแกรมนี้")
                    return
                
                # อ่านข้อมูลแถวแรกเพื่อดึงข้อมูลโครงการ/โรงเรียน
                first_row = True
                
                for row in reader:
                    try:
                        # ตั้งค่าโครงการและโรงเรียนจากแถวแรก
                        if first_row:
                            if row.get('โครงการ'):
                                self.project_name.set(row['โครงการ'])
                            if row.get('โรงเรียน'):
                                self.school_name.set(row['โรงเรียน'])
                            first_row = False
                        
                        # ตรวจสอบเลขบัตรซ้ำ
                        cid = row.get('เลขบัตรประชาชน', '').strip()
                        if not cid:
                            error_count += 1
                            continue
                        
                        # ตรวจสอบว่ามีข้อมูลซ้ำในระบบหรือไม่
                        is_duplicate = False
                        for existing_data in self.card_data_list:
                            if existing_data['cid'] == cid:
                                is_duplicate = True
                                duplicate_count += 1
                                break
                        
                        if is_duplicate:
                            continue
                        
                        # สร้าง card_info จากข้อมูลใน CSV
                        card_info = {
                            'cid': cid,
                            'th_title': row.get('คำนำหน้า (ไทย)', ''),
                            'th_firstname': row.get('ชื่อ (ไทย)', ''),
                            'th_lastname': row.get('นามสกุล (ไทย)', ''),
                            'en_title': row.get('คำนำหน้า (อังกฤษ)', ''),
                            'en_firstname': row.get('ชื่อ (อังกฤษ)', ''),
                            'en_lastname': row.get('นามสกุล (อังกฤษ)', ''),
                            'birth_date': row.get('วันเกิด', ''),
                            'gender': row.get('เพศ', ''),
                            'issuer': row.get('หน่วยงานออกบัตร', ''),
                            'issue_date': row.get('วันออกบัตร', ''),
                            'expire_date': row.get('วันหมดอายุ', ''),
                            'address_house_no': row.get('บ้านเลขที่', ''),
                            'address_moo_soi': row.get('หมู่/ซอย', ''),
                            'address_subdistrict': row.get('ตำบล/แขวง', ''),
                            'address_district': row.get('อำเภอ/เขต', ''),
                            'address_province': row.get('จังหวัด', ''),
                            'timestamp': row.get('วันที่อ่าน', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                        }
                        
                        # สร้าง fullname
                        th_parts = []
                        if card_info['th_title']:
                            th_parts.append(card_info['th_title'])
                        if card_info['th_firstname']:
                            th_parts.append(card_info['th_firstname'])
                        if card_info['th_lastname']:
                            th_parts.append(card_info['th_lastname'])
                        card_info['th_fullname'] = ' '.join(th_parts)
                        
                        en_parts = []
                        if card_info['en_title']:
                            en_parts.append(card_info['en_title'])
                        if card_info['en_firstname']:
                            en_parts.append(card_info['en_firstname'])
                        if card_info['en_lastname']:
                            en_parts.append(card_info['en_lastname'])
                        card_info['en_fullname'] = ' '.join(en_parts)
                        
                        # สร้าง fulladdress
                        addr_parts = []
                        if card_info['address_house_no']:
                            addr_parts.append(card_info['address_house_no'])
                        if card_info['address_moo_soi']:
                            addr_parts.append(card_info['address_moo_soi'])
                        if card_info['address_subdistrict']:
                            addr_parts.append(card_info['address_subdistrict'])
                        if card_info['address_district']:
                            addr_parts.append(card_info['address_district'])
                        if card_info['address_province']:
                            addr_parts.append(card_info['address_province'])
                        card_info['address'] = ' '.join(addr_parts)
                        
                        # เพิ่มข้อมูลลงในตาราง
                        self.card_data_list.append(card_info)
                        
                        index = len(self.card_data_list)
                        self.tree.insert("", END, values=(
                            index,
                            card_info['cid'],
                            card_info['th_fullname'],
                            card_info['en_fullname'],
                            card_info['birth_date'],
                            card_info['gender'],
                            card_info['timestamp']
                        ))
                        
                        imported_count += 1
                        
                    except Exception as e:
                        print(f"Error importing row: {e}")
                        error_count += 1
                        continue
            
            # อัพเดทจำนวน
            self.data_count.set(f"{len(self.card_data_list)} คน")
            
            # แสดงสรุปผลการ import
            summary = f"Import สำเร็จ: {imported_count} รายการ"
            if duplicate_count > 0:
                summary += f"\nข้อมูลซ้ำ: {duplicate_count} รายการ"
            if error_count > 0:
                summary += f"\nข้อมูลผิดพลาด: {error_count} รายการ"
            
            messagebox.showinfo("Import สำเร็จ", summary)
            
        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถ import ได้\n{str(e)}")
    
    def export_to_csv(self):
        """Export ข้อมูลเป็น CSV"""
        if not self.card_data_list:
            messagebox.showwarning("ไม่มีข้อมูล", "กรุณาอ่านบัตรอย่างน้อย 1 ใบ")
            return
        
        # สร้างชื่อไฟล์
        project = self.project_name.get() or "project"
        school = self.school_name.get() or "school"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{project}_{school}_{timestamp}.csv"
        
        # เลือกที่บันทึก
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    # Header - แยกคำนำหน้า ชื่อ นามสกุล และที่อยู่เป็นคอลัมน์ต่างหาก
                    fieldnames = [
                        'ลำดับ', 'โครงการ', 'โรงเรียน', 'เลขบัตรประชาชน',
                        'คำนำหน้า (ไทย)', 'ชื่อ (ไทย)', 'นามสกุล (ไทย)',
                        'คำนำหน้า (อังกฤษ)', 'ชื่อ (อังกฤษ)', 'นามสกุล (อังกฤษ)',
                        'วันเกิด', 'เพศ', 'หน่วยงานออกบัตร', 
                        'วันออกบัตร', 'วันหมดอายุ',
                        'บ้านเลขที่', 'หมู่/ซอย', 'ตำบล/แขวง', 'อำเภอ/เขต', 'จังหวัด',
                        'วันที่อ่าน'
                    ]
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Data
                    for index, data in enumerate(self.card_data_list, 1):
                        writer.writerow({
                            'ลำดับ': index,
                            'โครงการ': self.project_name.get(),
                            'โรงเรียน': self.school_name.get(),
                            'เลขบัตรประชาชน': data['cid'],
                            'คำนำหน้า (ไทย)': data.get('th_title', ''),
                            'ชื่อ (ไทย)': data.get('th_firstname', ''),
                            'นามสกุล (ไทย)': data.get('th_lastname', ''),
                            'คำนำหน้า (อังกฤษ)': data.get('en_title', ''),
                            'ชื่อ (อังกฤษ)': data.get('en_firstname', ''),
                            'นามสกุล (อังกฤษ)': data.get('en_lastname', ''),
                            'วันเกิด': data['birth_date'],
                            'เพศ': data['gender'],
                            'หน่วยงานออกบัตร': data['issuer'],
                            'วันออกบัตร': data['issue_date'],
                            'วันหมดอายุ': data['expire_date'],
                            'บ้านเลขที่': data.get('address_house_no', ''),
                            'หมู่/ซอย': data.get('address_moo_soi', ''),
                            'ตำบล/แขวง': data.get('address_subdistrict', ''),
                            'อำเภอ/เขต': data.get('address_district', ''),
                            'จังหวัด': data.get('address_province', ''),
                            'วันที่อ่าน': data['timestamp']
                        })
                
                messagebox.showinfo("สำเร็จ", f"Export ข้อมูลสำเร็จ!\n{filename}")
                
            except Exception as e:
                messagebox.showerror("ผิดพลาด", f"ไม่สามารถ export ได้\n{str(e)}")
    
    def clear_all_data(self):
        """ลบข้อมูลทั้งหมด"""
        if not self.card_data_list:
            return
        
        if messagebox.askyesno("ยืนยัน", "ต้องการลบข้อมูลทั้งหมดหรือไม่?"):
            self.card_data_list.clear()
            self.tree.delete(*self.tree.get_children())
            self.data_count.set("0 คน")
            self.current_cid = None
            messagebox.showinfo("สำเร็จ", "ลบข้อมูลทั้งหมดแล้ว")
    
    def refresh_reader(self):
        """รีเฟรช reader"""
        self.reader = None
        self.find_reader()
    
    def view_details(self):
        """ดูรายละเอียดของรายการที่เลือก"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("แจ้งเตือน", "กรุณาเลือกรายการที่ต้องการดู")
            return
        
        # Get selected item
        item = self.tree.item(selected[0])
        index = int(item['values'][0]) - 1
        data = self.card_data_list[index]
        
        # Create detail window
        detail_win = Toplevel(self.root)
        detail_win.title(f"รายละเอียด - {data['cid']}")
        detail_win.geometry("600x500")
        
        # Content
        frame = ttk.Frame(detail_win, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        details = [
            ("เลขบัตรประชาชน", data['cid']),
            ("ชื่อ-นามสกุล (ไทย)", data['th_fullname']),
            ("ชื่อ-นามสกุล (อังกฤษ)", data['en_fullname']),
            ("วันเกิด", data['birth_date']),
            ("เพศ", data['gender']),
            ("หน่วยงานออกบัตร", data['issuer']),
            ("วันออกบัตร", data['issue_date']),
            ("วันหมดอายุ", data['expire_date']),
            ("ที่อยู่", data['address']),
            ("วันที่อ่าน", data['timestamp'])
        ]
        
        for i, (label, value) in enumerate(details):
            # Use default font with bold for labels
            label_widget = ttk.Label(frame, text=f"{label}:")
            label_widget.grid(row=i, column=0, sticky=W, pady=5, padx=5)
            
            value_widget = ttk.Label(frame, text=value)
            value_widget.grid(row=i, column=1, sticky=W, pady=5, padx=5)
        
        ttk.Button(detail_win, text="ปิด", command=detail_win.destroy).pack(pady=10)
    
    def on_closing(self):
        """ปิดโปรแกรม"""
        self.monitoring = False
        self.root.destroy()


def main():
    root = Tk()
    
    # Set default font (use system font)
    try:
        # Try to use a Thai-compatible font if available
        import tkinter.font as tkfont
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=11)
    except:
        pass
    
    app = IDCardReaderGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
