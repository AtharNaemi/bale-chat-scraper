import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
import os
import re

def extract_clean_time(time_str):
    if not time_str or time_str == "نامشخص":
        return "00:00"
    persian_arabic_to_eng = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
    clean_str = str(time_str).translate(persian_arabic_to_eng)
    match = re.search(r'(\d{1,2}:\d{2})', clean_str)
    return match.group(1) if match else "00:00"

def clean_filename_content(text_str):
    if not text_str:
        return "نامشخص"
    clean_text = text_str.replace(" ", "_").replace(":", "_").replace("：", "_")
    clean_text = re.sub(r'[\\/*?:"<>|]', "", clean_text)
    return clean_text

def get_next_part_number(folder_path):
    if not os.path.exists(folder_path):
        return 1
    max_part = 0
    pattern = re.compile(r'^بخش_(\d+)_')
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            part_num = int(match.group(1))
            if part_num > max_part:
                max_part = part_num
    return max_part + 1

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./bale_user_data", 
            headless=False,
            channel="chrome"
        )
        page = await browser.new_page()
        await page.goto("https://web.bale.ai/")
        
        output_folder = "./bale_backups"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        # تشخیص خودکار پارت بعدی از روی فایل‌های موجود
        part_counter = get_next_part_number(output_folder)
        
        print("\n[!] وارد حساب بله شوید.")
        print("[!] چت را باز کنید و دستی ببرید روی همان نقطه شروع (مثلاً ۶ بهمن).")
        print(f"[i] سیستم به صورت خودکار پارت بعدی را شماره **{part_counter}** نام‌گذاری خواهد کرد.")
        input("[=>] پس از مستقر شدن در ابتدای چت، Enter بزنید تا ریزش واقعی رو به پایین شروع شود...")
        
        # فوکوس روی کانتینر چت
        await page.click(".CcBJaj")
        
        unique_messages = {}
        current_date_header = "نامشخص"
        loop_counter = 0
        infinity_loops = 1000000 
        last_saved_count = 0 
        
        print(f"\n[*] پرواز فوق‌سریع رو به پایین بدون سورت مزاحم...")
        
        while loop_counter < infinity_loops:
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.find_all(class_=['message-item', 'message-block', 'Wqgb2D'])
            
            for el in elements:
                try:
                    classes = el.get('class', [])
                    if 'Wqgb2D' in classes:
                        current_date_header = el.text.strip()
                        continue
                    
                    if any('hviPrH' in c for c in classes):
                        sender_name = "من"
                    else:
                        sender_name = "مخاطب"

                    text_el = el.find(class_=['KTwPFW', 'KTwPFW.YjkWXv'])
                    text = text_el.text.strip() if text_el else "[رسانه، تصویر یا فایل ضمیمه]"
                    
                    time_el = el.find(class_=['HXOHbT', 'bisANn'])
                    time_str = time_el.text.strip() if time_el else "نامشخص"
                    
                    msg_key = f"{current_date_header}_{time_str}_{text[:40]}"
                    
                    if msg_key not in unique_messages:
                        unique_messages[msg_key] = {
                            "تاریخ": current_date_header,
                            "فرستنده": sender_name,
                            "ساعت": time_str,
                            "متن پیام": text
                        }
                        
                        current_total = len(unique_messages)
                        if current_total > 0 and (current_total - last_saved_count) == 500:
                            all_list = list(unique_messages.values())
                            chunk_data = all_list[last_saved_count:current_total]
                            
                            # ساخت دیتافریم بدون سورت کردن تا ترتیب طبیعی حفظ شود
                            chunk_df = pd.DataFrame(chunk_data)
                            
                            # ماسک کردن تاریخ‌های تکراری پشت سر هم برای زیبایی فایل اکسل
                            chunk_df['تاریخ'] = chunk_df['تاریخ'].mask(chunk_df['تاریخ'].duplicated(), "")
                            
                            # نام فایل بر اساس اولین پیام این پارت (که حالا مطمئنیم قدیمی‌ترین پیام پارت است)
                            sample_time = extract_clean_time(chunk_data[0]["ساعت"])
                            sample_date = chunk_data[0]["تاریخ"]
                            
                            file_name = f"بخش_{part_counter}_[{clean_filename_content(sample_time)}]__{clean_filename_content(sample_date)}.csv"
                            file_path = os.path.join(output_folder, file_name)
                            chunk_df.to_csv(file_path, index=False, encoding="utf-8-sig")
                            
                            print(f"\n[✓] پارت {part_counter} با ترتیب ۱۰۰٪ خطی ذخیره شد: {file_name}")
                            last_saved_count = current_total
                            part_counter += 1
                except Exception:
                    continue
            
            # اسکرول فوق‌سریع رو به پایین
            await page.mouse.wheel(0, 6000)
            await page.wait_for_timeout(200) 
            
            loop_counter += 1
            print(f"   - پیام‌های ردیابی شده: {len(unique_messages)} | پله حرکت رو به پایین: {loop_counter}", end="\r")

        # ذخیره پارت باقی‌مانده آخر
        current_total = len(unique_messages)
        if current_total > last_saved_count:
            all_list = list(unique_messages.values())
            chunk_data = all_list[last_saved_count:current_total]
            chunk_df = pd.DataFrame(chunk_data)
            chunk_df['تاریخ'] = chunk_df['تاریخ'].mask(chunk_df['تاریخ'].duplicated(), "")
            
            sample_time = extract_clean_time(chunk_data[0]["ساعت"])
            sample_date = chunk_data[0]["تاریخ"]
            file_name = f"بخش_پایانی_ریزش_[{clean_filename_content(sample_time)}]__{clean_filename_content(sample_date)}.csv"
            file_path = os.path.join(output_folder, file_name)
            chunk_df.to_csv(file_path, index=False, encoding="utf-8-sig")
            print(f"\n[✓] پارت نهایی ریزش ذخیره شد: {file_name}")

        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n\n[!] توقف دستی. فایل‌ها تا این لحظه با ترتیب کاملاً درست ذخیره شدند.")