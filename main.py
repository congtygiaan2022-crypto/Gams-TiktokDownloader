import logging
import time
import sys
import os
import config
from gemlogin_api import GemLoginAPI
from gpm_login_api import GPMLoginAPI
from donut_api import DonutAPI
from browser import Browser
from tiktok_manager import TikTokManager
from downloader import Downloader
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import json
import random
import string
import requests

# Sửa lỗi hiển thị tiếng Việt trên console Windows
sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình logging an toàn với Unicode
class UnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Fallback nếu console không hỗ trợ Unicode
            msg = self.format(record).encode('ascii', 'replace').decode('ascii')
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        UnicodeStreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

import re

def sanitize_filename(name):
    """Loại bỏ ký tự không hợp lệ cho tên file Windows, bao gồm cả xuống dòng."""
    if not name:
        return ""
    # Thay thế các ký tự xuống dòng, tab bằng khoảng trắng
    name = re.sub(r'[\r\n\t]+', ' ', name)
    # Loại bỏ ký tự cấm: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    return name.strip()

def generate_random_hashtag(length=6):
    """Tạo hashtag ngẫu nhiên để tránh trùng tên file."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def extract_video_title(driver, video_url):
    """Trích xuất caption (mô tả) video từ trang TikTok."""
    def is_valid_caption(text):
        if not text: return False
        # Nếu chứa pattern profile stats "X Likes. . Y Followers" thì là sai
        if "Likes." in text and "Followers." in text and "·" in text:
            return False
        return True

    try:
        # Chờ tối đa 8 giây cho script rehydration xuất hiện để đảm bảo dữ liệu trang đã được tải
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.ID, "__UNIVERSAL_DATA_FOR_REHYDRATION__"))
            )
        except:
            pass

        # BƯỚC 1: Thử trích xuất từ JSON data (Đệ quy có chọn lọc) - ƯU TIÊN HÀNG ĐẦU
        try:
            script = """
                function findVideoDesc(obj) {
                    if (!obj || typeof obj !== 'object') return null;
                    
                    // Nếu object này có vẻ là ItemStruct (có desc và playAddr hoặc id)
                    if (obj.desc && (obj.playAddr || obj.id || obj.author)) {
                        return obj.desc;
                    }
                    
                    for (let key in obj) {
                        // Bỏ qua phần user detail để tránh lấy profile bio
                        if (key === 'webapp.user-detail' || key === 'userInfo' || key === 'user') continue;
                        
                        let res = findVideoDesc(obj[key]);
                        if (res) return res;
                    }
                    return null;
                }
                try {
                    let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                    if (!el) return null;
                    let data = JSON.parse(el.textContent);
                    return findVideoDesc(data);
                } catch(e) { return null; }
            """
            caption = driver.execute_script(script)
            if is_valid_caption(caption):
                logger.info(f"✓ Đã lấy caption từ JSON (Video-specific): {caption[:50]}...")
                return caption.strip()
        except Exception as e:
            logger.debug(f"Không lấy được caption từ JSON: {e}")

        # BƯỚC 2: Thử các selector DOM của trang chi tiết video (loại bỏ browse-video-desc để tránh lệch sang sidebar)
        selectors = [
            "h1[data-e2e='video-desc']",
            "span[data-e2e='video-desc'] span",
            "[data-e2e='video-desc']",
            "div[class*='DivDescription']",
            ".video-description"
        ]
        
        for selector in selectors:
            try:
                caption_el = driver.find_element(By.CSS_SELECTOR, selector)
                caption = caption_el.text.strip()
                if is_valid_caption(caption):
                    logger.info(f"✓ Đã lấy caption từ selector {selector}: {caption[:50]}...")
                    return caption
            except:
                continue

        # BƯỚC 3: Meta description (Last resort, với validation)
        try:
            meta_el = driver.find_element(By.CSS_SELECTOR, "meta[name='description']")
            caption = meta_el.get_attribute("content")
            # TikTok meta desc thường có format: "Caption | TikTok" hoặc "[Stats] | @user. Caption..."
            # Ta cố gắng tách lấy phần caption
            if is_valid_caption(caption):
                # Nếu meta chứa profile stats, thử cắt lấy phần sau dấu chấm cuối cùng hoặc sau username
                if "Likes. ·" in caption:
                    parts = caption.split("·")
                    if len(parts) > 2:
                        last_part = parts[-1].split("@")[-1].strip()
                        # Thường là "@username. CAPTION"
                        if "." in last_part:
                            real_caption = last_part.split(".", 1)[-1].strip()
                            if real_caption: return real_caption
                
                logger.info(f"✓ Đã lấy caption từ meta description: {caption[:50]}...")
                return caption.strip()
        except:
            pass
        
    except Exception as e:
        logger.warning(f"Lỗi khi trích xuất caption: {e}")
        return ""

def get_video_url_from_kituchat(driver, video_url):
    """Sử dụng kituchat.net để lấy link video chất lượng cao (HD) và caption."""
    try:
        logger.info(f"Đang lấy link từ KituCHAT cho: {video_url}")
        driver.get("https://kituchat.net/tai-video-tiktok/")
        time.sleep(random.uniform(2, 4))
        
        # Nhập URL
        input_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "params"))
        )
        input_el.clear()
        for char in video_url:
            input_el.send_keys(char)
            time.sleep(random.uniform(0.01, 0.05))
        
        # Click TẢI VỀ 3 LẦN hoặc đến khi có kết quả
        for i in range(3):
            try:
                # Kiểm tra xem đã có link tải chưa
                if i > 0:
                    all_btns = driver.find_elements(By.CSS_SELECTOR, ".result button, .result a, .btn-submit")
                    found_no_logo = False
                    for btn in all_btns:
                        btn_text = btn.text.upper()
                        if "NO WATERMARK" in btn_text or "KHÔNG LOGO" in btn_text:
                            logger.info(f"✓ Đã thấy nút tải không logo: {btn_text}")
                            found_no_logo = True
                            break
                    if found_no_logo: break

                # Tìm nút Tải về (màu đỏ)
                btn_tai_ve = driver.find_element(By.CSS_SELECTOR, ".btn-submit")
                btn_tai_ve.click()
                delay = random.uniform(3, 5)
                logger.info(f"Đã click 'Tải về' lần {i+1}/3. Đang chờ {delay:.1f}s...")
                time.sleep(delay)
            except Exception as e:
                logger.warning(f"Lỗi click 'Tải về' lần {i+1}: {e}")
        
        # Chờ kết quả hiện ra (thường là bảng link)
        time.sleep(random.uniform(4, 6))
        
        # 1. TRÍCH XUẤT TIÊU ĐỀ (CAPTION) TỪ TRANG KẾT QUẢ
        video_title = None
        try:
            # Tìm trong h3 hoặc các thẻ bold/mô tả
            title_selectors = ["h3", ".video-title", "div.ticket-res p", "div.ticket-info b"]
            for selector in title_selectors:
                try:
                    title_el = driver.find_element(By.CSS_SELECTOR, selector)
                    text = title_el.text.strip()
                    if text and "@" not in text and "Tải video" not in text and "Công cụ này" not in text:
                        video_title = text
                        logger.info(f"✓ Đã lấy tiêu đề từ KituCHAT: {video_title[:50]}...")
                        break
                except:
                    continue
        except Exception as e:
            logger.warning(f"Lỗi trích xuất tiêu đề từ KituCHAT: {e}")

        # 2. TÌM LINK TẢI - ƯU TIÊN NO WATERMARK HD -> NO WATERMARK
        all_btns = driver.find_elements(By.CSS_SELECTOR, ".result button, .result a, .btn-first, button.btn")
        
        # Priority 1: NO WATERMARK(HD)
        for btn in all_btns:
            try:
                text = btn.text.strip().upper()
                if "NO WATERMARK(HD)" in text or "KHÔNG LOGO (HD)" in text:
                    # Thử lấy href hoặc onclick
                    href = btn.get_attribute("href")
                    # Chỉ lấy nếu link không phải của TikTok gốc
                    if href and href.startswith("http") and not (href.startswith("https://www.tiktok.com/") or "/video/" in href):
                        logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 1): Tìm thấy {text} qua href")
                        return href, video_title
                    
                    onclick = btn.get_attribute("onclick")
                    if onclick:
                        match = re.search(r"['\"](https?://[^'\"]+)['\"]", onclick)
                        if match:
                            link = match.group(1)
                            logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 1): Tìm thấy {text} qua onclick")
                            return link, video_title
            except: continue

        # Priority 2: NO WATERMARK
        for btn in all_btns:
            try:
                text = btn.text.strip().upper()
                if "NO WATERMARK" in text and "(HD)" not in text:
                    href = btn.get_attribute("href")
                    if href and href.startswith("http") and not (href.startswith("https://www.tiktok.com/") or "/video/" in href):
                        logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 2): Tìm thấy {text} qua href")
                        return href, video_title
                    
                    onclick = btn.get_attribute("onclick")
                    if onclick:
                        match = re.search(r"['\"](https?://[^'\"]+)['\"]", onclick)
                        if match:
                            link = match.group(1)
                            logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 2): Tìm thấy {text} qua onclick")
                            return link, video_title
            except: continue

        # Fallback regex search in source (Most reliable for KituCHAT HD)
        try:
            page_content = driver.page_source
            hd_links = re.findall(r'"hdplay"\s*:\s*"([^"]+)"', page_content)
            if hd_links:
                link = hd_links[0].encode().decode('unicode_escape') if '\\u' in hd_links[0] else hd_links[0]
                if not (link.startswith("https://www.tiktok.com/") or "/video/" in link):
                    logger.info(f"✓ THÀNH CÔNG (Regex HD): Lấy link HD sạch logo từ script")
                    return link, video_title
        except: pass

        return None, video_title
    except Exception as e:
        logger.error(f"Lỗi KituCHAT: {e}")
        return None, None


def get_video_url_from_lovetik(driver, video_url):
    """Sử dụng vi.lovetik.com để lấy link video chất lượng cao."""
    try:
        logger.info(f"Đang lấy link từ Lovetik cho: {video_url}")
        driver.get("https://vi.lovetik.com/")
        time.sleep(random.uniform(2, 4))
        
        # Nhập URL
        input_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "k__input"))
        )
        input_el.clear()
        for char in video_url:
            input_el.send_keys(char)
            time.sleep(random.uniform(0.01, 0.05))
        
        # Click Bắt đầu
        btn_start = driver.find_element(By.ID, "btn-start")
        btn_start.click()
        
        # Chờ kết quả hiện ra (thường là bảng link)
        time.sleep(random.uniform(4, 6))
        
        # TÌM LINK TẢI VỚI ƯU TIÊN CHẶT CHẼ
        rows = driver.find_elements(By.CSS_SELECTOR, ".result_list tr, .result_list li, tr, li")
        
        # Danh sách ưu tiên theo yêu cầu người dùng
        priorities = [
            "MP4 HD ORIGINAL",
            "MP4 HD 1080P",
            "MP4 720P",
            "NO WATERMARK",
            "HD"
        ]
        
        for priority in priorities:
            for row in rows:
                try:
                    row_text = " ".join(row.text.upper().split())
                    # Tuyệt đối không tải video có logo (trừ khi có NO đứng trước WATERMARK)
                    if "WATERMARK" in row_text and "NO" not in row_text:
                        continue
                        
                    if priority in row_text:
                        link_el = row.find_element(By.TAG_NAME, "a")
                        href = link_el.get_attribute("href")
                        # CHỐNG LOGO: Tuyệt đối không lấy link dẫn trực tiếp về tiktok.com
                        if href and not (href.startswith("https://www.tiktok.com/") or "/video/" in href):
                            logger.info(f"✓ THÀNH CÔNG (Lovetik): Tìm thấy {priority} (Link sạch)")
                            return href, None
                except: continue

        return None, None
    except Exception as e:
        logger.error(f"Lỗi Lovetik: {e}")
        return None, None
def remove_hashtags(title):
    if not title:
        return ""
    # Remove hashtags starting with # or ＃ (full-width)
    clean = re.sub(r'[#＃]\S+', '', title)
    # Clean up multiple spaces and strip
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def download_and_save_video(driver, video_url, channel_name, tk_manager, downloader, copy_channels=None):
    """Xử lý trích xuất thông tin chi tiết và tải video/slideshow."""
    try:
        logger.info(f"🚀 BẮT ĐẦU TẢI: {video_url}")
        
        # 1. Trích xuất thông tin từ trang video gốc
        video_title = extract_video_title(driver, video_url)
        if getattr(config, 'EXTRACT_STATS', True):
            extract_video_stats(driver)
            
        direct_url = video_url
        slideshow_images = []
        
        # 1.1 Trích xuất link video hoặc slideshow qua JSON đệ quy
        try:
            extract_data_script = """
                function findMedia(obj) {
                    if (!obj || typeof obj !== 'object') return null;
                    if (obj.imagePost && obj.imagePost.images) {
                        return { type: 'slideshow', images: obj.imagePost.images.map(img => img.imageURL.urlList[0]) };
                    }
                    if (obj.playAddr && obj.playAddr.urlList) {
                        return { type: 'video', url: obj.playAddr.urlList[0] };
                    }
                    for (let key in obj) {
                        let res = findMedia(obj[key]);
                        if (res) return res;
                    }
                    return null;
                }
                try {
                    let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                    if (!el) return null;
                    let data = JSON.parse(el.textContent);
                    return findMedia(data);
                } catch(e) { return null; }
            """
            media_data = driver.execute_script(extract_data_script)
            if media_data:
                if media_data['type'] == 'slideshow' and getattr(config, 'DOWNLOAD_SLIDESHOW', True):
                    slideshow_images = media_data.get('images', [])
                elif media_data['type'] == 'video':
                    direct_url = media_data.get('url', video_url)
        except Exception as e:
            logger.warning(f"Lỗi trích xuất JSON đệ quy: {e}")

        # 2. LẤY LINK SẠCH LOGO (Ưu tiên KituCHAT -> Lovetik -> TikWM)
        play_url = None
        
        # Nguồn 1: KituCHAT HD
        play_url, k_title = get_video_url_from_kituchat(driver, video_url)
        if k_title and not video_title: video_title = k_title
            
        # Nguồn 2: Lovetik
        if not play_url:
            play_url, l_title = get_video_url_from_lovetik(driver, video_url)
            if l_title and not video_title: video_title = l_title
        
        # Nguồn 3: TikWM
        if not play_url:
            play_url_fallback, images_fallback, title_fallback = get_video_url_from_tikwm(video_url)
            if play_url_fallback:
                play_url = play_url_fallback
                logger.info("✓ Dùng TikWM làm nguồn dự phòng.")
            if images_fallback and not slideshow_images:
                slideshow_images = images_fallback
            if title_fallback and not video_title:
                video_title = title_fallback

        if play_url:
            direct_url = play_url
            
        if not play_url and not slideshow_images:
            logger.error(f"❌ THẤT BẠI: Không tìm thấy link video sạch logo cho {video_url}")
            return

        # 3. Thư mục và Tên file
        target_dir = os.path.join(config.DOWNLOAD_PATH, channel_name)
        os.makedirs(target_dir, exist_ok=True)
        
        # Xử lý Slideshow
        if slideshow_images:
            post_id = video_url.split('/')[-1].split('?')[0]
            clean_title = remove_hashtags(video_title) if video_title else ""
            # Fallback nếu tiêu đề trống
            if not clean_title:
                slide_dir_name = f"slideshow_{post_id}"
            else:
                slide_dir_name = sanitize_filename(clean_title[:50])
                if not slide_dir_name:
                    slide_dir_name = f"slideshow_{post_id}"
            slide_path = os.path.join(target_dir, slide_dir_name)
            os.makedirs(slide_path, exist_ok=True)
            
            all_success = True
            for idx, img_url in enumerate(slideshow_images):
                save_img_path = os.path.join(slide_path, f"image_{idx+1}.jpg")
                if not downloader.download_direct_url(img_url, save_img_path):
                    all_success = False
            
            if all_success:
                tk_manager.update_history(video_url)
                # Lưu report download ngay lập tức
                tk_manager.add_to_download_report(channel_name, video_url, slide_dir_name)
                logger.info(f"✓ [Xong Slideshow] {video_url}")
                
                if copy_channels:
                    for copy_ch in copy_channels:
                        target_name = copy_ch.get('name') or channel_name
                        if target_name != channel_name:
                            dest_dir = os.path.join(config.DOWNLOAD_PATH, target_name)
                            os.makedirs(dest_dir, exist_ok=True)
                            dest_path = os.path.join(dest_dir, slide_dir_name)
                            if not os.path.exists(dest_path):
                                try:
                                    import shutil
                                    shutil.copytree(slide_path, dest_path)
                                    logger.info(f"✓ Đã copy slideshow sang {target_name}")
                                    tk_manager.add_to_download_report(target_name, video_url, slide_dir_name)
                                except Exception as e:
                                    logger.error(f"Lỗi copy slideshow sang {target_name}: {e}")
            return all_success

        # Xử lý Video đơn lẻ
        if video_title:
            clean_title = remove_hashtags(video_title)
            # Fallback nếu tiêu đề trống
            if not clean_title:
                video_id = video_url.split('/')[-1].split('?')[0]
                random_tag = generate_random_hashtag(6)
                save_name = f"video_{video_id}_#{random_tag}.mp4"
            else:
                safe_title = sanitize_filename(clean_title)
                if len(safe_title) > 80: safe_title = safe_title[:80].strip()
                if not safe_title:
                    video_id = video_url.split('/')[-1].split('?')[0]
                    random_tag = generate_random_hashtag(6)
                    save_name = f"video_{video_id}_#{random_tag}.mp4"
                else:
                    random_tag = generate_random_hashtag(6)
                    save_name = f"{safe_title} #{random_tag}.mp4"
        else:
            video_id = video_url.split('/')[-1].split('?')[0]
            random_tag = generate_random_hashtag(6)
            save_name = f"video_{video_id}_#{random_tag}.mp4"
            
        save_path = os.path.join(target_dir, save_name)
        
        # Tải xuống
        cookies_dict = {c['name']: c['value'] for c in driver.get_cookies()}
        ua = driver.execute_script("return navigator.userAgent;")
        
        success = downloader.download_direct_url(direct_url, save_path, cookies_dict=cookies_dict, user_agent=ua)
        if success:
            tk_manager.update_history(video_url)
            # Lưu report download ngay lập tức
            tk_manager.add_to_download_report(channel_name, video_url, save_name)
            logger.info(f"✓ [Thành công] {save_name}")
            
            if copy_channels:
                for copy_ch in copy_channels:
                    target_name = copy_ch.get('name') or channel_name
                    if target_name != channel_name:
                        dest_dir = os.path.join(config.DOWNLOAD_PATH, target_name)
                        os.makedirs(dest_dir, exist_ok=True)
                        dest_path = os.path.join(dest_dir, save_name)
                        if not os.path.exists(dest_path):
                            try:
                                import shutil
                                shutil.copy2(save_path, dest_path)
                                logger.info(f"✓ Đã copy video sang {target_name}")
                                tk_manager.add_to_download_report(target_name, video_url, save_name)
                            except Exception as e:
                                logger.error(f"Lỗi copy video sang {target_name}: {e}")
        else:
            logger.error(f"✗ [Lỗi tải] {video_url}")
        return success
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình tải {video_url}: {e}")
        return False


def extract_video_stats(driver):
    """Trích xuất thống kê (Like, Comment, Share) từ trang TikTok sử dụng tìm kiếm đệ quy."""
    try:
        script = """
            function findStats(obj) {
                if (obj && typeof obj === 'object') {
                    if (obj.stats && obj.stats.diggCount !== undefined) return obj.stats;
                    if (obj.statistics && obj.statistics.diggCount !== undefined) return obj.statistics;
                    for (let key in obj) {
                        let res = findStats(obj[key]);
                        if (res) return res;
                    }
                }
                return null;
            }
            try {
                let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                if (!el) return null;
                let data = JSON.parse(el.textContent);
                let stats = findStats(data);
                if (stats) {
                    return {
                        digg_count: stats.diggCount || stats.digg_count || 0,
                        comment_count: stats.commentCount || stats.comment_count || 0,
                        collect_count: stats.collectCount || stats.collect_count || 0,
                        share_count: stats.shareCount || stats.share_count || 0,
                        play_count: stats.playCount || stats.play_count || 0
                    };
                }
            } catch(e) { return null; }
            return null;
        """
        stats = driver.execute_script(script)
        if stats:
            logger.info(f"📊 Thống kê: ❤️ {stats['digg_count']} | 💬 {stats['comment_count']} |  SHARE {stats['share_count']}")
            return stats
        return None
    except Exception as e:
        logger.warning(f"Lỗi trích xuất thống kê: {e}")
        return None
def copy_existing_download(video_url, origin_channel_name, copy_channels, tk_manager):
    """
    Tìm kiếm file/thư mục đã tải trước đó của video_url trong thư mục origin_channel_name,
    và copy sang các thư mục khác trong copy_channels nếu chưa có.
    """
    if not copy_channels or len(copy_channels) <= 1:
        return
    
    # 1. Tìm tên file/thư mục từ report file
    report_file = getattr(config, 'DOWNLOAD_REPORT_FILE', 'tải video tiktok.txt')
    filename = None
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Đọc ngược hoặc duyệt tìm dòng khớp video_url
                for line in f:
                    if video_url in line and " | File: " in line:
                        parts = line.split(" | File: ")
                        if len(parts) > 1:
                            filename = parts[1].strip()
        except Exception as e:
            logger.warning(f"Lỗi đọc report file {report_file}: {e}")
            
    # 2. Nếu không tìm thấy trong report, thử tìm trên đĩa (quét thư mục gốc theo ID video)
    video_id = video_url.split('/')[-1].split('?')[0]
    origin_dir = os.path.join(config.DOWNLOAD_PATH, origin_channel_name)
    
    if not filename and os.path.exists(origin_dir):
        try:
            for item in os.listdir(origin_dir):
                if video_id in item:
                    filename = item
                    break
        except Exception as e:
            logger.warning(f"Lỗi duyệt thư mục gốc {origin_dir}: {e}")
            
    if not filename:
        logger.warning(f"Không tìm thấy tên file/thư mục lưu trước đó cho {video_url} để thực hiện copy.")
        return

    # 3. Tiến hành copy sang các thư mục đích
    src_path = os.path.join(origin_dir, filename)
    if not os.path.exists(src_path):
        logger.warning(f"File nguồn không tồn tại trên đĩa để copy: {src_path}")
        return

    is_dir = os.path.isdir(src_path)
    import shutil
    
    for copy_ch in copy_channels:
        target_name = copy_ch.get('name') or origin_channel_name
        if target_name == origin_channel_name:
            continue
            
        dest_dir = os.path.join(config.DOWNLOAD_PATH, target_name)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        
        if not os.path.exists(dest_path):
            try:
                if is_dir:
                    shutil.copytree(src_path, dest_path)
                    logger.info(f"✓ Đã copy thư mục slideshow đã tải trước đó sang {target_name}: {filename}")
                else:
                    shutil.copy(src_path, dest_path)
                    logger.info(f"✓ Đã copy video đã tải trước đó sang {target_name}: {filename}")
                
                # Ghi nhận vào báo cáo tải cho thư mục đích
                if tk_manager:
                    tk_manager.add_to_download_report(target_name, video_url, filename)
            except Exception as e:
                logger.error(f"Lỗi copy {filename} sang {target_name}: {e}")

def close_tiktok_login_modal(driver):
    """
    Tự động phát hiện và đóng cửa sổ đăng nhập (login modal) của TikTok nếu xuất hiện.
    """
    try:
        # Cách 1: Gửi phím ESCAPE tới body để đóng các dialog/modal nhanh
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    except:
        pass

    # Cách 2: Tìm các nút Đóng modal bằng XPath
    selectors = [
        "//div[contains(@id, 'login-modal')]//div[contains(@class, 'close')]",
        "//button[@aria-label='Close']",
        "//div[contains(@class, 'login-modal')]//button",
        "//*[@data-e2e='modal-close-button']",
        "//div[contains(@class, 'ModalClose')]//button",
        "//div[contains(@class, 'modal')]//div[contains(@class, 'close')]",
        "//button[contains(@class, 'close')]"
    ]
    
    for xpath in selectors:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    try:
                        el.click()
                    except:
                        driver.execute_script("arguments[0].click();", el)
                    logger.info("✓ Đã click đóng login popup của TikTok.")
                    time.sleep(1)
                    return True
        except:
            continue
    return False

def check_and_resolve_something_went_wrong(driver, channel_url, max_attempts=3):
    """
    Kiểm tra xem trang có bị lỗi 'Something went wrong' hay không.
    Nếu có, tự động nhấn nút Refresh hoặc tải lại trang.
    Trả về True nếu phát hiện và đã xử lý (hoặc đang xử lý), False nếu không bị lỗi.
    Trả về 'SOMETHING_WENT_WRONG' nếu đã thử hết số lần mà vẫn bị lỗi.
    """
    for attempt in range(max_attempts):
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
        except:
            page_text = ""

        if "something went wrong" in page_text.lower():
            logger.warning(f"Lỗi 'Something went wrong' xuất hiện trên kênh {channel_url}. Đang thử click Refresh lần {attempt + 1}/{max_attempts}...")
            clicked = False
            xpaths = [
                "//button[text()='Refresh']",
                "//button[contains(text(), 'Refresh')]",
                "//*[text()='Refresh']",
                "//div[text()='Refresh']",
                "//button[contains(@class, 'refresh')]",
                "//*[contains(@class, 'Refresh')]"
            ]
            for xpath in xpaths:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    for el in elements:
                        if el.is_displayed() and el.is_enabled():
                            try:
                                el.click()
                            except:
                                driver.execute_script("arguments[0].click();", el)
                            clicked = True
                            break
                    if clicked:
                        break
                except:
                    pass
            if not clicked:
                logger.info("Không tìm thấy nút Refresh bằng selector, đang reload trang bằng driver.refresh()...")
                driver.refresh()
            
            time.sleep(5)
            close_tiktok_login_modal(driver)
        else:
            if attempt > 0:
                logger.info(f"✓ Đã vượt qua lỗi 'Something went wrong' sau khi refresh.")
                return True
            return False

    # Check one last time
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
    except:
        page_text = ""
    if "something went wrong" in page_text.lower():
        logger.error(f"Lỗi 'Something went wrong' vẫn tồn tại sau {max_attempts} lần refresh trên kênh {channel_url}!")
        return "SOMETHING_WENT_WRONG"
    return True

def scrape_channel(driver, channel_url, tk_manager=None, downloader=None, max_videos=config.MAX_VIDEOS_PER_CHANNEL, copy_channels=None):
    """
    Quét các video TikTok mới nhất từ profile bằng cách nhấp vào từng post 
    để lấy URL CHÍNH XÁC từ thanh địa chỉ (Address Bar). 
    THỰC HIỆN TẢI XUỐNG NGAY LẬP TỨC CHO MỖI VIDEO TÌM THẤY.
    """
    count = 0
    try:
        logger.info(f"📡 ĐANG QUÉT KÊNH: {channel_url}")
        driver.get(channel_url)
        close_tiktok_login_modal(driver)

        # Check for early page load issues (Die or Something went wrong)
        sww_res = check_and_resolve_something_went_wrong(driver, channel_url, max_attempts=4)
        if sww_res == "SOMETHING_WENT_WRONG":
            return "SOMETHING_WENT_WRONG"

        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
        except:
            page_text = ""

        # Check for "Die" account early
        die_indicators = [
            "Couldn't find this account",
            "Looking for videos? Try browsing our trending creators"
        ]
        if any(ind in page_text for ind in die_indicators):
            logger.warning(f"Kênh {channel_url} có vẻ đã bị xóa hoặc die (check early).")
            return "DIE"

        wait = WebDriverWait(driver, 15)
        
        # Lấy tên người dùng
        channel_title = "unknown_tiktok"
        try:
            title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-title']")))
            channel_title = title_el.text.strip()
        except:
            if "@" in channel_url: channel_title = channel_url.split("@")[-1].split("?")[0]
        
        logger.info(f"Phát hiện TikToker: {channel_title}")

        # Xác định tên thư mục lưu ngay từ đầu
        final_dir_name = sanitize_filename(channel_title)
        
        if copy_channels:
            assigned_names = []
            for idx, ch in enumerate(copy_channels):
                # Nếu user chưa gán tên (name là None/empty)
                # Hoặc name đang là placeholder cũ "tên kênh"
                if not ch.get('name') or ch['name'] == "tên kênh" or ch['name'] == f"tên kênh {idx+1}":
                    new_name = final_dir_name if idx == 0 else f"{final_dir_name} {idx + 1}"
                    ch['name'] = new_name
                assigned_names.append(ch['name'])
                
            if tk_manager:
                tk_manager.update_group_names(channel_url, assigned_names)
            final_dir_name = copy_channels[0]['name']
        else:
            if tk_manager:
                tk_manager.update_channel_name(channel_url, final_dir_name)

        history = set()
        if tk_manager: history = tk_manager.get_downloaded_history()

        # Check for "Die" account
        die_indicators = [
            "Couldn't find this account",
            "Looking for videos? Try browsing our trending creators"
        ]
        # Thử tìm nhanh text trên page
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if any(ind in page_text for ind in die_indicators):
                logger.warning(f"Kênh {channel_url} có vẻ đã bị xóa hoặc die.")
                return "DIE"
        except: pass

        # Lưu ID của tab chính (Profile TikTok)
        main_tab = driver.current_window_handle

        post_selector = "//*[@data-e2e='user-post-item']"
        posts = []
        for attempt in range(5):
            close_tiktok_login_modal(driver)
            posts = driver.find_elements(By.XPATH, post_selector)
            if posts:
                logger.info(f"Đã tìm thấy {len(posts)} bài viết trên DOM.")
                break
            
            # Check for 'Something went wrong' during post load attempt
            sww_res = check_and_resolve_something_went_wrong(driver, channel_url, max_attempts=2)
            if sww_res == "SOMETHING_WENT_WRONG":
                return "SOMETHING_WENT_WRONG"
            elif sww_res is True:
                # Nếu đã refresh lại trang, ta cần tìm lại posts từ đầu
                posts = driver.find_elements(By.XPATH, post_selector)
                if posts:
                    logger.info(f"Đã tìm thấy {len(posts)} bài viết trên DOM sau khi refresh lỗi.")
                    break
            
            try:
                # Đợi ngắn xem phần tử xuất hiện không
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, post_selector))
                )
                posts = driver.find_elements(By.XPATH, post_selector)
                if posts:
                    break
            except:
                pass
                
            # Cuộn xuống để kích hoạt load (kể cả kênh có Playlist làm đẩy grid video xuống dưới)
            scroll_amt = (attempt + 1) * 400
            logger.info(f"Chưa tìm thấy bài viết, cuộn xuống {scroll_amt}px (Lần thử {attempt + 1}/5)...")
            driver.execute_script(f"window.scrollTo(0, {scroll_amt});")
            time.sleep(2)
            
        # Cuộn lại lên đầu để chuẩn bị quét từ video đầu tiên
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1.5)

        posts = driver.find_elements(By.XPATH, post_selector)
        if not posts:
            logger.warning(f"Không tìm thấy bài viết nào cho kênh {channel_url}. Có thể trang chưa load kịp.")
            return 0
            
        logger.info(f"Tìm thấy bài viết trên trang. Sẽ kiểm tra {min(len(posts), max_videos)} video gần nhất.")
        
        # count = 0 # Đã init ở đầu function
        posts_to_check = min(len(posts), max_videos)
        for i in range(posts_to_check):
            try:
                # ĐẢM BẢO QUAY VỀ TRANG PROFILE NẾU ĐANG KẸT TRÌNH XEM VIDEO
                for _ in range(3):
                    if "/video/" not in driver.current_url and "/photo/" not in driver.current_url:
                        break
                    logger.info("Đang thoát trình xem video để về trang profile...")
                    driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(2)
                    if "/video/" in driver.current_url or "/photo/" in driver.current_url:
                        driver.get(channel_url)
                        time.sleep(3)

                # Refresh list posts
                current_posts = driver.find_elements(By.XPATH, post_selector)
                if i >= len(current_posts): 
                    logger.warning(f"Chỉ tìm thấy {len(current_posts)} video, dừng quét (dự kiến {max_videos}).")
                    break
                post = current_posts[i]
                
                close_tiktok_login_modal(driver)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post)
                time.sleep(0.5)
                
                # Check history sơ bộ qua href nếu có
                try:
                    video_link_el = post.find_element(By.TAG_NAME, "a")
                    post_href = video_link_el.get_attribute("href")
                    if post_href:
                        full_url = post_href.split('?')[0].rstrip('/')
                        if history and full_url in history:
                            logger.info(f"Bỏ qua (đã tải): {full_url}")
                            copy_existing_download(full_url, final_dir_name, copy_channels, tk_manager)
                            continue
                except: pass

                # Mở và lấy link video
                video_loaded = False
                for click_attempt in range(3):
                    try:
                        close_tiktok_login_modal(driver)
                        # Click vào post
                        try:
                            post.click()
                        except:
                            driver.execute_script("arguments[0].click();", post)
                        
                        # Đợi URL thay đổi hoặc player xuất hiện
                        for _ in range(5):
                            if "/video/" in driver.current_url or "/photo/" in driver.current_url:
                                video_loaded = True
                                break
                            time.sleep(1)
                        if video_loaded: break
                    except:
                        time.sleep(2)
                
                if video_loaded:
                    full_url = driver.current_url.split('?')[0].rstrip('/')
                    if history and full_url in history:
                        logger.info(f"Bỏ qua (đã tải): {full_url}")
                        copy_existing_download(full_url, final_dir_name, copy_channels, tk_manager)
                    else:
                        logger.info(f"👉 Xử lý video {count+1}/{max_videos}...")
                        logger.info(f"🔗 Đấu nối: {full_url}")
                        
                        # 1. Mở tab mới và chờ handle an toàn
                        main_handle = driver.current_window_handle
                        try:
                            driver.switch_to.new_window('tab')
                        except Exception as e:
                            logger.warning(f"Lỗi tạo tab bằng new_window, thử JS: {e}")
                            driver.execute_script("window.open('');")
                            time.sleep(1)
                            if driver.window_handles[-1] == main_handle:
                                raise Exception("Không thể mở tab tải mới (bị chặn popup?)")
                            driver.switch_to.window(driver.window_handles[-1])
                        
                        # 2. Thực hiện tải
                        try:
                            driver.get(full_url)
                            time.sleep(3)
                            download_and_save_video(driver, full_url, final_dir_name, tk_manager, downloader, copy_channels=copy_channels)
                        finally:
                            # Luôn đóng tất cả các tab phụ (kể cả popup ads) và về tab chính
                            try:
                                current_handles = driver.window_handles
                                if main_handle in current_handles:
                                    for h in list(current_handles):
                                        if h != main_handle:
                                            try:
                                                driver.switch_to.window(h)
                                                driver.close()
                                                time.sleep(0.2)
                                            except:
                                                pass
                                    driver.switch_to.window(main_handle)
                                else:
                                    # Nếu mất main_handle, giữ lại tab đầu tiên làm main_handle mới
                                    if current_handles:
                                        main_handle = current_handles[0]
                                        for h in list(current_handles)[1:]:
                                            try:
                                                driver.switch_to.window(h)
                                                driver.close()
                                                time.sleep(0.2)
                                            except:
                                                pass
                                        driver.switch_to.window(main_handle)
                            except Exception as win_err:
                                logger.warning(f"Lỗi dọn dẹp các tab phụ: {win_err}")

                        count += 1
                else:
                    logger.warning("Không lấy được link video hoặc không thể mở bài viết.")

                # Đóng player trên tab chính
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1.5)

            except Exception as e:
                logger.warning(f"Lỗi khi xử lý bài viết thứ {i+1}: {e}")
                # Kiểm tra mất session ngay tại đây
                is_session_lost = False
                try:
                    _ = driver.current_window_handle
                except Exception as driver_err:
                    is_session_lost = True
                    logger.error(f"Phát hiện mất kết nối trình duyệt khi xử lý bài viết: {driver_err}")

                if is_session_lost or "invalid session id" in str(e).lower() or "no such window" in str(e).lower():
                    raise e

                # Đảm bảo quay về tab chính nếu lỗi
                try: 
                    if driver.current_window_handle != main_handle:
                        driver.close()
                    driver.switch_to.window(main_handle)
                except: pass
                continue
            
        return count
    except Exception as e:
        # Thử kiểm tra xem driver còn sống hay đã mất kết nối hoàn toàn
        is_session_lost = False
        try:
            _ = driver.current_window_handle
        except Exception as driver_err:
            is_session_lost = True
            logger.error(f"Phát hiện mất kết nối trình duyệt: {driver_err}")

        if is_session_lost or "invalid session id" in str(e).lower() or "no such window" in str(e).lower():
            logger.error(f"Lỗi mất session khi quét TikTok {channel_url}: {e}")
            raise e 
        logger.error(f"Lỗi khi quét TikTok {channel_url}: {e}")
        return count

def start_browser_session(api, browser_handler, profile_id):
    """Khởi động profile và kết nối selenium, trả về driver."""
    # ĐẢM BẢO PROFILE ĐÃ DỪNG TRƯỚC KHI MỞ (Tránh lỗi debugger address rỗng)
    try:
        logger.info(f"Đang kiểm tra và đóng profile {profile_id} nếu đang chạy...")
        api.stop_profile(profile_id)
        time.sleep(2)
    except:
        pass

    logger.info(f"Đang khởi động profile {profile_id}...")
    try:
        # Thử khởi động tối đa 2 lần nếu lần đầu trả về rỗng
        result = {}
        for attempt in range(2):
            result = api.start_profile(profile_id)
            if result and (result.get('http') or result.get('selenium_remote_debug_address') or result.get('port')):
                break
            if attempt == 0:
                logger.warning("Kết quả khởi động rỗng, thử đóng lại và khởi động lại...")
                api.stop_profile(profile_id)
                time.sleep(3)
        
        debugger_address = result.get('http') or result.get('selenium_remote_debug_address') or result.get('remote_debugging_address')
        driver_path = result.get('driver_path')
        
        if not debugger_address:
            # Dự phòng dùng port
            port = result.get('port')
            if port:
                debugger_address = f"127.0.0.1:{port}"
        
        if not debugger_address:
            logger.error(f"Không lấy được địa chỉ debugger từ kết quả khởi động: {result}")
            return None

        logger.info(f"Địa chỉ debugger: {debugger_address}")
        return browser_handler.attach(debugger_address, driver_path=driver_path)
    except Exception as e:
        logger.error(f"Lỗi khởi động/kết nối session: {e}")
        return None

import requests

def get_video_url_from_tikwm(video_url):
    """Sử dụng API TikWM (bên thứ 3) để lấy link tải video không watermark và caption."""
    try:
        logger.info(f"Đang thử lấy link từ TikWM cho: {video_url}")
        api_url = "https://www.tikwm.com/api/"
        payload = {'url': video_url, 'hd': 1}
        response = requests.post(api_url, data=payload, timeout=15)
        
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get('code') == 0:
                data = res_json.get('data', {})
                title = data.get('title')
                
                # Ưu tiên link video
                play_url = data.get('play')
                images = data.get('images')
                
                if play_url:
                    logger.info("✓ Lấy link video và caption thành công từ TikWM.")
                    return play_url, None, title
                
                if images:
                    logger.info(f"✓ Lấy thành công slideshow ({len(images)} ảnh) và caption từ TikWM.")
                    return None, images, title
        
        logger.warning(f"TikWM không trả về kết quả cho: {video_url}")
        return None, None, None
    except Exception as e:
        logger.error(f"Lỗi khi gọi API TikWM: {e}")
        return None, None, None

def _build_api():
    """Tạo API object phù hợp với BROWSER_TYPE trong config."""
    browser_type = getattr(config, 'BROWSER_TYPE', 'gemlogin').lower()
    if browser_type == 'gpmlogin':
        logger.info("Sử dụng trình duyệt: GPM Login")
        return GPMLoginAPI()
    elif browser_type == 'donut':
        logger.info("Sử dụng trình duyệt: Donut Browser")
        return DonutAPI()
    elif browser_type in ('chrome', 'cococ'):
        logger.info(f"Sử dụng trình duyệt: {'Chrome' if browser_type == 'chrome' else 'Cốc Cốc'} (native)")
        return None  # Chrome/CốcCốc không cần API
    else:
        logger.info("Sử dụng trình duyệt: GemLogin")
        return GemLoginAPI()


def _get_profile_list(api):
    """
    Lấy danh sách profile từ GemLogin / GPM Login.
    Trả về list các dict profile.
    """
    try:
        profiles = api.get_profiles()
        return profiles if profiles else []
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách profile: {e}")
        return []


def _select_profile(profiles):
    """
    Chọn profile dựa trên config:
    - Nếu SELECTED_PROFILE_ID có giá trị → dùng trực tiếp
    - Ngược lại tìm theo SELECTED_PROFILE_NAME
    - Fallback: profile đầu tiên trong danh sách
    """
    selected_id = getattr(config, 'SELECTED_PROFILE_ID', '').strip()
    target_name = getattr(config, 'SELECTED_PROFILE_NAME', 'Tải video tiktok').strip()

    if selected_id:
        # Ưu tiên dùng ID đã lưu
        matched = next((p for p in profiles if
                        str(p.get('id') or p.get('uuid') or p.get('profile_id')) == selected_id), None)
        if matched:
            return matched
        logger.warning(f"Không tìm thấy profile ID '{selected_id}'. Thử tìm theo tên...")

    if target_name:
        matched = next((p for p in profiles if target_name.lower() in (p.get('name') or '').lower()), None)
        if matched:
            return matched
        logger.warning(f"Không tìm thấy profile tên '{target_name}'. Dùng profile đầu tiên.")

    return profiles[0] if profiles else None


def _start_native_browser(browser_handler):
    """
    Khởi động Chrome hoặc Cốc Cốc bằng subprocess (không qua API).
    Trả về driver hoặc None.
    """
    browser_type = getattr(config, 'BROWSER_TYPE', 'chrome').lower()

    if browser_type == 'chrome':
        return browser_handler.launch_chrome(
            user_data_dir=getattr(config, 'CHROME_USER_DATA_DIR', ''),
            profile_name=getattr(config, 'CHROME_PROFILE_NAME', 'Default'),
            debug_port=getattr(config, 'CHROME_DEBUG_PORT', 9222),
            chrome_exe=getattr(config, 'CHROME_EXE_PATH', '') or None,
        )
    elif browser_type == 'cococ':
        return browser_handler.launch_cococ(
            user_data_dir=getattr(config, 'COCOC_USER_DATA_DIR', ''),
            profile_name=getattr(config, 'COCOC_PROFILE_NAME', 'Default'),
            debug_port=getattr(config, 'COCOC_DEBUG_PORT', 9223),
            cococ_exe=getattr(config, 'COCOC_EXE_PATH', '') or None,
        )
    return None

def start_browser_session_donut(api, browser_handler, profile_id):
    """
    Khởi động profile Donut Browser và kết nối Selenium.
    Donut API POST /v1/profiles/{id}/run → trả về {'remote_debugging_port': 9222}
    """
    # Dừng trước để tảnh xung đột
    try:
        logger.info(f"[Donut] Kiểm tra và đóng profile {profile_id} nếu đang chạy...")
        api.stop_profile(profile_id)
        time.sleep(2)
    except:
        pass

    logger.info(f"[Donut] Khởi động profile {profile_id}...")
    try:
        debugger_address = None
        for attempt in range(2):
            debugger_address = api.start_profile(profile_id)
            if debugger_address:
                break
            if attempt == 0:
                logger.warning("[Donut] Không lấy được port, thử lại...")
                api.stop_profile(profile_id)
                time.sleep(3)

        if not debugger_address:
            logger.error("[Donut] Không lấy được debugger address từ Donut API.")
            return None

        logger.info(f"[Donut] Debugger address: {debugger_address}")
        return browser_handler.attach(debugger_address)
    except Exception as e:
        logger.error(f"[Donut] Lỗi khởi động session: {e}")
        return None


def main():
    import random as _random

    browser_type = getattr(config, 'BROWSER_TYPE', 'gemlogin').lower()
    is_donut = (browser_type == 'donut')
    use_api_browser = browser_type in ('gemlogin', 'gpmlogin', 'donut')

    api = _build_api()  # None nếu Chrome/CốcCốc
    browser_handler = Browser()

    tk_manager = TikTokManager()
    downloader = Downloader()

    profile_id = None           # ID đang chạy (GemLogin/GPM)
    all_profiles = []           # Danh sách tất cả profiles (cho rotate)
    rotate_profiles = getattr(config, 'ROTATE_PROFILES', False)
    rotate_interval = max(1, getattr(config, 'PROFILE_ROTATE_INTERVAL', 5))
    rotate_order = getattr(config, 'PROFILE_ROTATE_ORDER', 'sequential')
    rotate_index = 0            # Con trỏ profile hiện tại trong danh sách
    channel_count_since_rotate = 0

    try:
        # ----------------------------------------------------------------
        # 1. Lấy profile phù hợp với loại browser
        # ----------------------------------------------------------------
        if use_api_browser:
            logger.info("Đang lấy danh sách profiles...")
            all_profiles = _get_profile_list(api)
            if not all_profiles:
                logger.error("Không tìm thấy profile nào. Vui lòng kiểm tra ứng dụng quản lý browser.")
                return

            selected_profile = _select_profile(all_profiles)
            if not selected_profile:
                logger.error("Không chọn được profile hợp lệ.")
                return

            profile_id = (selected_profile.get('id') or
                          selected_profile.get('uuid') or
                          selected_profile.get('profile_id'))
            if not profile_id:
                logger.error(f"Không xác định được ID profile: {selected_profile}")
                return

            logger.info(f"Đã chọn profile: {selected_profile.get('name')} (ID: {profile_id})")

            # Nếu rotate bật → build danh sách profile để xoay
            if rotate_profiles and len(all_profiles) > 1:
                # Đặt profile hiện tại là điểm bắt đầu trong danh sách xoay
                try:
                    rotate_index = all_profiles.index(selected_profile)
                except ValueError:
                    rotate_index = 0
                logger.info(f"Chế độ Rotate Profile BẬT — {len(all_profiles)} profiles, mỗi {rotate_interval} kênh.")

            # Khởi động ban đầu
            if is_donut:
                driver = start_browser_session_donut(api, browser_handler, profile_id)
            else:
                driver = start_browser_session(api, browser_handler, profile_id)
        else:
            # Chrome / Cốc Cốc native
            logger.info(f"Đang khởi động {'Chrome' if browser_type == 'chrome' else 'Cốc Cốc'}...")
            driver = _start_native_browser(browser_handler)

        if not driver:
            logger.error("Khởi động trình duyệt thất bại.")
            return

        # ----------------------------------------------------------------
        # 2. Xử lý danh sách kênh TikTok
        # ----------------------------------------------------------------
        channels_data = tk_manager.get_channels()

        from collections import defaultdict
        grouped_channels = defaultdict(list)
        for ch in channels_data:
            grouped_channels[ch['url']].append(ch)

        channel_groups = list(grouped_channels.items())

        for idx, (channel_url, channels_in_group) in enumerate(channel_groups):

            # --- Rotate Profile (chỉ khi dùng API browser và bật rotate) ---
            if (use_api_browser and rotate_profiles and len(all_profiles) > 1
                    and channel_count_since_rotate >= rotate_interval and idx > 0):

                logger.info(f"[Rotate] Đã xử lý {channel_count_since_rotate} kênh. Đang đổi profile...")
                try:
                    browser_handler.close()
                    api.stop_profile(profile_id)
                    time.sleep(3)
                except Exception:
                    pass

                # Chọn profile tiếp theo
                if rotate_order == 'random':
                    next_profile = _random.choice(all_profiles)
                else:  # sequential
                    rotate_index = (rotate_index + 1) % len(all_profiles)
                    next_profile = all_profiles[rotate_index]

                profile_id = (next_profile.get('id') or
                              next_profile.get('uuid') or
                              next_profile.get('profile_id'))
                logger.info(f"[Rotate] Chuyển sang profile: {next_profile.get('name')} (ID: {profile_id})")

                if is_donut:
                    driver = start_browser_session_donut(api, browser_handler, profile_id)
                else:
                    driver = start_browser_session(api, browser_handler, profile_id)

                if not driver:
                    logger.error("Không thể khởi động profile mới. Dừng rotate, thử khởi động lại profile cũ...")
                    if is_donut:
                        driver = start_browser_session_donut(api, browser_handler, profile_id)
                    else:
                        driver = start_browser_session(api, browser_handler, profile_id)
                    if not driver:
                        logger.error("Không thể tiếp tục. Thoát.")
                        return

                channel_count_since_rotate = 0

            # --- Xử lý từng kênh ---
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if not driver:
                        raise Exception("Driver is None")

                    res = scrape_channel(
                        driver, channel_url,
                        tk_manager=tk_manager,
                        downloader=downloader,
                        copy_channels=channels_in_group
                    )

                    if res == "DIE":
                        tk_manager.update_channel_status(channel_url, "kênh die")
                    elif res == "SOMETHING_WENT_WRONG":
                        tk_manager.update_channel_status(channel_url, "kênh lỗi Something went wrong")
                    else:
                        tk_manager.update_channel_status(channel_url, "kênh live")
                        logger.info(f"✓ Hoàn tất kênh {channel_url}. Đã tải {res} video mới.")

                    channel_count_since_rotate += 1
                    break

                except Exception as e:
                    logger.warning(f"Lỗi xử lý TikTok {channel_url} (Lần thử {attempt+1}/{max_retries}): {e}")
                    logger.info("Đang khởi động lại session trình duyệt...")
                    try:
                        browser_handler.close()
                    except:
                        pass

                    if use_api_browser:
                        try:
                            api.stop_profile(profile_id)
                        except:
                            pass
                        time.sleep(5)
                        if is_donut:
                            driver = start_browser_session_donut(api, browser_handler, profile_id)
                        else:
                            driver = start_browser_session(api, browser_handler, profile_id)
                    else:
                        time.sleep(5)
                        driver = _start_native_browser(browser_handler)

                    if not driver:
                        logger.error("Không thể khởi động lại session. Bỏ qua kênh này.")
                        break

        # ----------------------------------------------------------------
        # 3. Hoàn tất
        # ----------------------------------------------------------------
        logger.info("Hoàn tất tất cả kênh. Đang đóng trình duyệt...")
        browser_handler.close()
        if use_api_browser and profile_id:
            api.stop_profile(profile_id)
            profile_id = None

    except Exception as e:
        logger.exception(f"Có lỗi xảy ra: {e}")

    finally:
        if browser_handler.driver:
            browser_handler.close()

        if use_api_browser and profile_id:
            logger.info(f"Đang dừng profile {profile_id}...")
            try:
                api.stop_profile(profile_id)
            except:
                pass
            logger.info("Hoàn tất.")


if __name__ == "__main__":
    main()
