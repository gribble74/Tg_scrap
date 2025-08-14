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
        # Базовые данные
        date_link = wrap.find('a', class_='tgme_widget_message_date')
        link = date_link['href'] if date_link else None
        date = date_link.find('time')['datetime'] if date_link and date_link.find('time') else str(datetime.now())
        
        # Текст сообщения
        text_div = wrap.find('div', class_='tgme_widget_message_text')
        text = str(text_div) if text_div else None
        
        # Медиа (фото)
        media = None
        photo_wrap = wrap.find('a', class_='tgme_widget_message_photo_wrap')
        if photo_wrap and 'style' in photo_wrap.attrs:
            style = photo_wrap['style']
            if 'background-image:' in style:
                media = style.split("url('")[1].split("')")[0] if "url('" in style else None
        
        # Видео (ищем превью)
        video_thumb = wrap.find('i', class_='tgme_widget_message_video_thumb')
        if video_thumb and 'style' in video_thumb.attrs:
            style = video_thumb['style']
            if 'background-image:' in style:
                media = style.split("url('")[1].split("')")[0] if "url('" in style else None
        
        return {
            'date': date,
            'link': link,
            'text': text.strip() if text else '',
            'media': media,
            'has_media': bool(media),
            'has_text': bool(text and text.strip())
        }
        
    except Exception as e:
        print(f"Error parsing post: {e}")
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
