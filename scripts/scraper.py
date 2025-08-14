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
                if post and post.get('text') and post['text'].strip() != '':
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
        
        # Текст сообщения с HTML-разметкой
        text_div = wrap.find('div', class_='tgme_widget_message_text')
        if not text_div:
            return None
            
        # Сохраняем оригинальную HTML-разметку
        text = ''.join(str(child) for child in text_div.contents)
        
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
        
        # Если видео без превью - пропускаем
        if video and not media:
            return None
            
        return {
            'date': date,
            'link': link,
            'text': text,
            'media': media,
            'has_media': bool(media),
            'has_text': bool(text)
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
        print(f"Successfully saved {len(posts)} posts")
    except Exception as e:
        print(f"Error saving posts: {e}")

if __name__ == "__main__":
    all_posts = get_all_posts()
    save_posts(all_posts)
