import os
import time
from datetime import datetime, timezone, timedelta
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotoVideo, InputMessagesFilterDocument
import piexif
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

def download_media(api_id, api_hash, phone, channel_or_chat, destination_directory, limit=100, delay=3, start_date=None):
    client = TelegramClient('umap_session', api_id, api_hash, 
                            system_version="Windows 10 x64", 
                            device_model="20S1S64W0X",
                            system_lang_code="ru-RU",
                            lang_code="en",
                            app_version="1.0.1a")
    client.start(phone)

    try:
        entity = client.get_entity(channel_or_chat)
        try:
            entity_name = entity.title
        except:
            entity_name = entity.username
    except:
        print(f"Cannot find any channel, group or chat using {channel_or_chat} of {type(channel_or_chat)} type")
        quit()
        
    save_path = os.path.join(destination_directory, entity_name)
    if os.path.exists(save_path):
        os.rename(save_path, save_path + '_' + datetime.now().strftime('%Y_%m_%d-%H_%M_%S'))

    os.makedirs(os.path.join(save_path, 'Photos'))
    os.makedirs(os.path.join(save_path, 'Videos'))

    for download_type in [InputMessagesFilterPhotoVideo, InputMessagesFilterDocument]:
        offset_id = 0
        counter = 0
        might_be_media = True

        while might_be_media:
            
            messages_iterator = client.iter_messages(entity=entity, limit=limit, offset_id=offset_id, filter=download_type)
            if not list(messages_iterator):
                break
            
            for message in messages_iterator:
                if start_date and (message.date + time_delta) < start_date:
                    print(f"Date {start_date_input} reached, done searching with filter {download_type.__name__.replace('InputMessagesFilter', '')}")
                    might_be_media = False
                    break

                media_date = message.forward.date if message.forward else message.date
                media_date = media_date + time_delta
                media_date_str = media_date.strftime('%Y_%m_%d-%H_%M_%S')

                if 'image/' in message.file.mime_type:
                    media_type = 'Photos'
                elif 'video/' in message.file.mime_type:
                    media_type = 'Videos'
                else:
                    offset_id = message.id
                    continue

                file = message.media

                try:
                    input_file = client.download_media(file)
                except:
                    print(f"Cannot download file from message id: {message.id}, date: {media_date_str}, skipping")
                    offset_id = message.id
                    continue
                
                file_extension = message.file.ext.lower()

                img_idx = 0 
                while True:
                    if img_idx == 0:
                        output_file = os.path.join(save_path, media_type, f"{media_date_str}{file_extension.replace('heic', 'jpg')}")
                    else:
                        output_file = os.path.join(save_path, media_type, f"{media_date_str}-{img_idx}{file_extension.replace('heic', 'jpg')}")
                
                    if os.path.exists(output_file):
                        img_idx += 1
                    else:
                        break
                        
                if (download_type == InputMessagesFilterPhotoVideo and file_extension == '.jpg') or file_extension == '.heic':
                    img = Image.open(input_file)
                    
                    if file_extension == '.heic':
                        img = Image.open(input_file)
                        exif = img.getexif()
                        exif_bytes = exif.tobytes()
                    else:
                        exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, 'Interop': {}, '1st': {}, 'thumbnail': None} 
                        exif_dict['0th'][306] = media_date.strftime('%Y:%m:%d %H:%M:%S') 
                        exif_bytes = piexif.dump(exif_dict)
                        
                    img.save(output_file, format='jpeg', exif=exif_bytes)
                    os.remove(input_file)
                else:   
                    os.rename(input_file, output_file)
                    
                counter += 1
                print(f"{counter}/{messages_iterator.total}: {output_file.replace(f"{save_path}\\", '')}")

                time.sleep(delay)
                    
                offset_id = message.id
                
    client.disconnect()

if __name__ == "__main__":
    api_id = input("Enter your API ID: ")
    api_hash = input("Enter your API Hash: ")
    phone = input("Enter your phone number: ")
    channel_or_chat = input("Enter the channel/chat name or ID: ")
    start_date_input = input("Enter the start date (YYYY-MM-DD), leave empty if not needed: ")
    
    destination_directory = "downloads"
    time_delta = timedelta(hours=3)
   
    try:
        channel_or_chat = int(channel_or_chat)
    except:
        pass

    if start_date_input:
        start_date = datetime.strptime(start_date_input, '%Y-%m-%d').replace(tzinfo=timezone.utc) + time_delta
    else:
        start_date = None

    download_media(api_id, api_hash, phone, channel_or_chat, destination_directory, limit=50, start_date=start_date)