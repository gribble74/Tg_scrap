import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
from urllib.parse import urljoin
import re

CHANNEL_NAME = "ordendog"
BASE_URL = f"https://t.me/s/{CHANNEL_NAME}"
OUTPUT_FILE = "../data/posts.json"
MAX_POSTS = 20

def clean_html(text):
    """Очищает HTML от лишних вложений и Telegram-специфичных элементов"""
    if not text:
        return ""
    
    # Удаляем все вложенные div с классом tgme_widget_message_text
    while '<div class="tgme_widget_message_text">' in text:
        text = text.replace('<div class="tgme_widget_message_text">', '').replace('</div>', '')
    
    # Удаляем атрибуты js-message_text
    text = text.replace('js-message_text', '')
    
    # Очищаем emoji-теги Telegram
    text = re.sub(r'<i class="emoji"[^>]*>(.*?)</i>', r'\1', text)
    
    # Удаляем пустые теги
    text = re.sub(r'<[^>]+>\s*</[^>]+>', '', text)
    
    # Заменяем <br> на переносы строк
    text = text.replace('<br>', '\n')
    
    return text.strip()

def parse_post(wrap):
    try:
        # Базовые данные
        date_link = wrap.find('a', class_='tgme_widget_message_date')
        link = date_link['href'] if date_link else None
        date = date_link.find('time')['datetime'] if date_link and date_link.find('time') else str(datetime.now())
        
        # Текст сообщения
        text_div = wrap.find('div', class_='tgme_widget_message_text')
        if not text_div:
            return None
        
        # Получаем очищенный HTML
        text = clean_html(str(text_div))
        
        # Медиа (фото/видео)
        media = None
        photo_wrap = wrap.find('a', class_='tgme_widget_message_photo_wrap')
        if photo_wrap and 'style' in photo_wrap.attrs:
            style = photo_wrap['style']
            if 'url(' in style:
                media = style.split("url('")[1].split("')")[0]
        
        # Видео (ищем превью)
        video = wrap.find('video')
        if video and 'poster' in video.attrs:
            media = video['poster']
        
        # Если нет ни текста, ни медиа - пропускаем пост
        if not text.strip() and not media:
            return None
            
        return {
            'date': date,
            'link': link,
            'text': text,
            'media': media,
            'has_media': bool(media),
            'has_text': bool(text.strip())
        }
        
    except Exception as e:
        print(f"Error parsing post: {e}")
        return None

def get_all_posts():
    posts = []
    url = BASE_URL
    session = requests.Session()
    
    while len(posts) < MAX_POSTS:
        try:
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            post_wraps = soup.find_all('div', class_='tgme_widget_message_wrap')
            
            if not post_wraps:
                break
                
            for wrap in reversed(post_wraps):
                post = parse_post(wrap)
                if post:
                    posts.append(post)
                    if len(posts) >= MAX_POSTS:
                        break
            
            prev_link = soup.find('a', class_='tme_messages_more')
            if not prev_link or len(posts) >= MAX_POSTS:
                break
                
            prev_url = prev_link.get('href')
            url = urljoin(BASE_URL, prev_url)
            
        except Exception as e:
            print(f"Error getting posts: {e}")
            break
    
    return posts[:MAX_POSTS]

def save_posts(posts):
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'last_updated': str(datetime.now()),
                'posts': posts
            }, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(posts)} posts to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving posts: {e}")

if __name__ == "__main__":
    print(f"Starting scraping of {CHANNEL_NAME} Telegram channel...")
    all_posts = get_all_posts()
    save_posts(all_posts)
    print("Scraping completed!")
