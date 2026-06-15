import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./bale_user_data", 
            headless=False,
            channel="chrome"
        )
        page = await browser.new_page()
        await page.goto("https://web.bale.ai/")
        
        print("\n[!] وارد حساب بله شوید و حتماً چت مورد نظر را باز کنید.")
        input("[=>] پس از باز شدن کامل چت، Enter بزنید تا ساختار صفحه را آنالیز کنم...")
        
        # گرفتن کل HTML صفحه
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # پیدا کردن تمام تگ‌های div و استخراج کلاس‌های آن‌ها
        all_divs = soup.find_all('div')
        seen_classes = set()
        report = []
        
        for div in all_divs:
            classes = div.get('class')
            if classes:
                class_str = ".".join(classes)
                if class_str not in seen_classes:
                    seen_classes.add(class_str)
                    # گرفتن کمی از متن داخل این المان برای تشخیص کاربرد آن
                    text_preview = div.text.strip()[:50].replace('\n', ' ')
                    report.append(f"Class: .{class_str}  |  Preview: {text_preview}")
        
        # ذخیره گزارش در یک فایل متنی
        with open("bale_structure_report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(report))
            
        print("\n[✓] آنالیز تمام شد! فایل 'bale_structure_report.txt' ایجاد شد.")
        print("لطفاً چند خط اول یا بخش‌هایی از این فایل که شبیه به پیام‌ها یا باکس چت هستند را اینجا بفرست.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())