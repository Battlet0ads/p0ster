from flask import Flask, render_template, request, redirect, url_for
import requests
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB

# Токены и ID
VK_TOKEN = 'vk1.a.e94vqmjbGPlIi9_dpLo-xyLmvQQM3PGDr1CJqwnlhwll960nNlJVtRIfF2AZjUaBL-aZlPTS82LxA2S7iRf5EMtFSfZCHZhtUXrt4WZhxpJhhFNHwruBj1KBLRJezMZtM3z9hmlMePnW4ZTeB-Ewa1648Lsnh8oodDlxUhxU7NPTTKaHTPsaZiyjeLApE47WzkLCF1ypMBm8Fx_YC8f_zQ'
TELEGRAM_TOKEN = '6422609683:AAH5FFfb-8QnmUoBQoDOt682kzilEYvB5ss'
VK_OWNER_ID = '-189467856'
TELEGRAM_CHAT_ID = '@alptorg'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/post', methods=['POST'])
def post():
    message = request.form['message']
    image = request.files['image'] if 'image' in request.files else None
    image_path = None
    vk_photo_url = None

    if image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)

    # Отправка поста в ВК
    if image_path:
        vk_upload_url = f'https://api.vk.com/method/photos.getWallUploadServer?access_token={VK_TOKEN}&v=5.131'
        upload_server_response = requests.get(vk_upload_url).json()
        upload_url = upload_server_response['response']['upload_url']

        with open(image_path, 'rb') as img:
            vk_upload_response = requests.post(upload_url, files={'photo': img}).json()

        vk_save_url = f'https://api.vk.com/method/photos.saveWallPhoto?access_token={VK_TOKEN}&v=5.131'
        vk_save_response = requests.post(vk_save_url, data={
            'server': vk_upload_response['server'],
            'photo': vk_upload_response['photo'],
            'hash': vk_upload_response['hash'],
            'access_token': VK_TOKEN
        }).json()

        media_id = f"photo{vk_save_response['response'][0]['owner_id']}_{vk_save_response['response'][0]['id']}"

        vk_post_url = f'https://api.vk.com/method/wall.post'
        vk_response = requests.post(vk_post_url, data={
            'owner_id': VK_OWNER_ID,
            'message': message,
            'attachments': media_id,
            'access_token': VK_TOKEN,
            'v': '5.131'
        })

        vk_photo_url = f"https://vk.com/photo{vk_save_response['response'][0]['owner_id']}_{vk_save_response['response'][0]['id']}"
    else:
        vk_post_url = f'https://api.vk.com/method/wall.post'
        vk_response = requests.post(vk_post_url, data={
            'owner_id': VK_OWNER_ID,
            'message': message,
            'access_token': VK_TOKEN,
            'v': '5.131'
        })

    vk_post = vk_response.json()
    vk_post_id = vk_post['response']['post_id']
    vk_post_url = f"https://vk.com/wall{VK_OWNER_ID}_{vk_post_id}"

    # Отправка поста в Telegram
    if image_path:
        telegram_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto'
        with open(image_path, 'rb') as img:
            telegram_response = requests.post(telegram_url, data={
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': message,
                'reply_markup': f'{{"inline_keyboard":[[{{"text":"Забрать заказ","url":"{vk_post_url}"}}]]}}'
            }, files={'photo': img})
    else:
        telegram_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        telegram_response = requests.post(telegram_url, data={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'reply_markup': f'{{"inline_keyboard":[[{{"text":"Забрать заказ","url":"{vk_post_url}"}}]]}}'
        })

    if vk_response.status_code == 200 and telegram_response.status_code == 200:
        return 'Post was successfully published!'
    else:
        return 'Failed to publish post.'


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=81)