import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

CHANNEL_URL = "https://t.me/s/ordendog"
OUTPUT_FILE = "../data/posts.json"
MAX_POSTS = 20

def scrape_telegram_channel():
    try:
        # Получаем HTML страницы с параметром before (для получения более старых постов)
        base_url = "https://t.me/s/ordendog?before="
        posts = []
        next_page_id = None
        
        while len(posts) < MAX_POSTS:
            # Формируем URL для запроса
            url = CHANNEL_URL if next_page_id is None else f"{base_url}{next_page_id}"
            
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            post_elements = soup.find_all('div', class_='tgme_widget_message_wrap')
            
            if not post_elements:
                break  # Больше нет постов
                
            # Обрабатываем посты в обратном порядке (новые сверху)
            for post in reversed(post_elements):
                try:
                    message = post.find('div', class_='tgme_widget_message_text')
                    if not message:
                        continue
                        
                    text = message.get_text('\n').strip()
                    date_element = post.find('time', class_='time')
                    date = date_element['datetime'] if date_element else str(datetime.now())
                    link = post.find('a', class_='tgme_widget_message_date')['href']
                    
                    media = post.find('a', class_='tgme_widget_message_photo_wrap')
                    media_url = media['style'].split("url('")[1].split("')")[0] if media else None
                    
                    # Проверяем, нет ли уже этого поста в списке
                    if not any(p['link'] == link for p in posts):
                        posts.append({
                            'text': text,
                            'date': date,
                            'link': link,
                            'media_url': media_url
                        })
                        
                        if len(posts) >= MAX_POSTS:
                            break
                except Exception as e:
                    print(f"Error parsing post: {e}")
                    continue
            
            # Находим ID для следующей страницы
            if len(posts) < MAX_POSTS:
                oldest_post = post_elements[0]
                next_page_id = oldest_post.find('a', class_='tgme_widget_message_date')['href'].split('/')[-1]
            else:
                break
        
        # Сортируем посты по дате (новые сверху)
        posts.sort(key=lambda x: x['date'], reverse=True)
        
        # Обрезаем до MAX_POSTS
        posts = posts[:MAX_POSTS]
        
        # Сохраняем в JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'last_updated': str(datetime.now()),
                'posts': posts
            }, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully scraped {len(posts)} posts")
        
    except Exception as e:
        print(f"Error scraping channel: {e}")

if __name__ == "__main__":
    scrape_telegram_channel()                media = post.find('a', class_='tgme_widget_message_photo_wrap')
                media_url = media['style'].split("url('")[1].split("')")[0] if media else None
                
                posts.append({
                    'text': text,
                    'date': date,
                    'link': link,
                    'media_url': media_url
                })
            except Exception as e:
                print(f"Error parsing post: {e}")
                continue
        
        # Сохраняем в JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'last_updated': str(datetime.now()),
                'posts': posts
            }, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully scraped {len(posts)} posts")
        
    except Exception as e:
        print(f"Error scraping channel: {e}")

if __name__ == "__main__":
    scrape_telegram_channel()
