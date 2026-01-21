import os
import re
import time
import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. ĐỊNH NGHĨA HÀM TẢI FILE (Giữ nguyên như cũ) ---
def download_file_from_js_link(driver, href_string, output_folder):
    pattern = r"downloadfile\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)"
    match = re.search(pattern, href_string)
    
    if not match:
        print(f"❌ Không phân tích được link: {href_string}")
        return None
        
    file_name = match.group(1)
    relative_url = match.group(2)
    base_url = "https://vbpl.vn" # Domain gốc
    download_url = base_url + relative_url
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    save_path = os.path.join(output_folder, file_name)
    
    session = requests.Session()
    selenium_cookies = driver.get_cookies()
    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    session.headers.update({"User-Agent": "Mozilla/5.0"}) # Fake user agent đơn giản

    print(f"⬇️ Đang tải: {file_name} ...")
    try:
        response = session.get(download_url, verify=False, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Đã lưu tại: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

# --- 2. CHƯƠNG TRÌNH CHÍNH (Phần bạn đang thiếu/sai) ---
if __name__ == "__main__":
    # A. KHỞI TẠO DRIVER (Đây là phần bạn bị thiếu dẫn đến lỗi NameError)
    driver = webdriver.Chrome() 
    
    try:
        # B. MỞ TRANG WEB CẦN TẢI
        # Bạn hãy thay URL dưới đây bằng URL thực tế chứa cái văn bản bạn muốn tải
        url_can_tai = "https://vbpl.vn/tw/Pages/vbpq-van-ban-goc.aspx?ItemID=123002" 
        driver.get(url_can_tai)
        
        # Chờ trang load xong (đơn giản nhất là sleep, hoặc dùng WebDriverWait nếu chuyên sâu hơn)
        time.sleep(3)

        # C. TÌM PHẦN TỬ VÀ GỌI HÀM
        # ID này lấy từ code HTML bạn gửi ban đầu
        element_id = "42.2017.QH14.docx" 
        
        # Kiểm tra xem phần tử có tồn tại không trước khi get_attribute
        elements = driver.find_elements(By.ID, element_id)
        
        if len(elements) > 0:
            link_element = elements[0]
            js_link = link_element.get_attribute("href")
            
            # Thư mục lưu file
            my_folder = r"D:\PTIT\VBPL\Data" 
            
            # Gọi hàm tải
            download_file_from_js_link(driver, js_link, my_folder)
        else:
            print(f"⚠️ Không tìm thấy phần tử có ID: {element_id}")

    except Exception as e:
        print(f"Lỗi chương trình: {e}")
        
    finally:
        # Đóng trình duyệt (tùy bạn muốn đóng hay không)
        # driver.quit()
        pass