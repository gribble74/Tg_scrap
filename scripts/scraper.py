import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
from urllib.parse import urljoin

CHANNEL_NAME = "ordendog"
BASE_URL = f"https://t.me/s/{CHANNEL_NAME}"
OUTPUT_FILE = "../data/posts.json"
MAX_POSTS = 20

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
                if post and (post.get('has_text') or post.get('has_media')):
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

def parse_post(wrap):
    try:
        date_link = wrap.find('a', class_='tgme_widget_message_date')
        if not date_link:
            return None
            
        link = date_link['href']
        date = date_link.find('time')['datetime'] if date_link.find('time') else None
        if not date:
            return None

        text_div = wrap.find('div', class_='tgme_widget_message_text')
        text = str(text_div) if text_div else ''
        
        # Получаем медиа в максимальном качестве
        media_url = None
        media_type = None
        
        # 1. Проверяем фото (оригиналы)
        photo_link = wrap.find('a', class_='tgme_widget_message_photo_wrap')
        if photo_link and photo_link.get('href'):
            media_url = photo_link['href'].replace('t.me/', 'cdn4.telesco.pe/file/') + '.jpg'
            media_type = 'photo'
        
        # 2. Проверяем видео
        if not media_url:
            video = wrap.find('video')
            if video and video.get('src'):
                media_url = video['src']
                media_type = 'video'
        
        # 3. Проверяем превью (fallback)
        if not media_url:
            thumb = wrap.find('i', class_='tgme_widget_message_video_thumb')
            if thumb and 'style' in thumb.attrs:
                style = thumb['style']
                if 'background-image:' in style:
                    media_url = style.split("url('")[1].split("')")[0]
                    media_type = 'video'
        
        return {
            'date': date,
            'link': link,
            'text': text.strip(),
            'media': normalize_media_url(media_url),
            'media_type': media_type,
            'has_media': bool(media_url),
            'has_text': bool(text.strip())
        }
    except Exception as e:
        logging.error(f"Error parsing post: {e}", exc_info=True)
        return None
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
    print(f"Scraping posts from {BASE_URL}...")
    all_posts = get_all_posts()
    save_posts(all_posts)
