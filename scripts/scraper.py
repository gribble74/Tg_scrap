import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
from urllib.parse import urljoin
import re
from bs4.element import Comment

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
                    if not any(p['link'] == post['link'] for p in posts):
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

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def clean_html(text_div):
    # Удаляем все теги кроме разрешенных
    allowed_tags = ['b', 'strong', 'i', 'em', 'a', 'br', 'span']
    soup = BeautifulSoup(text_div, 'html.parser')
    
    # Конвертируем эмодзи Telegram в Unicode
    for emoji in soup.find_all('i', class_='emoji'):
        emoji.replace_with(emoji.get_text())
    
    # Удаляем все неразрешенные теги
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()
    
    # Очищаем атрибуты (оставляем только href для ссылок)
    for tag in soup.find_all(True):
        if tag.name == 'a':
            attrs = {'href': tag.get('href', '')}
            tag.attrs = attrs
        else:
            tag.attrs = {}
    
    return str(soup)

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
            
        # Получаем чистый HTML с сохранением форматирования
        text = clean_html(str(text_div))
        
        # Медиа (фото/видео/документы)
        media = None
        media_type = None
        
        # Фото
        photo_wrap = wrap.find('a', class_='tgme_widget_message_photo_wrap')
        if photo_wrap and 'style' in photo_wrap.attrs:
            style = photo_wrap['style']
            if 'url(' in style:
                media = style.split("url('")[1].split("')")[0]
                media_type = 'photo'
        
        # Видео
        video = wrap.find('video')
        if video:
            if 'poster' in video.attrs:
                media = video['poster']
                media_type = 'video'
            elif 'src' in video.attrs:
                media = video['src']
                media_type = 'video'
        
        # Документы
        document = wrap.find('a', class_='tgme_widget_message_document')
        if document and 'href' in document.attrs:
            media = document['href']
            media_type = 'document'
        
        return {
            'date': date,
            'link': link,
            'text': text,
            'media': media,
            'media_type': media_type,
            'has_media': bool(media),
            'has_text': bool(text.strip())
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
