import os
import time
from datetime import datetime, timezone, timedelta
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import piexif

def download_photos(api_id, api_hash, phone, channel_or_chat, destination_directory, limit=100, delay=3, start_date=None):
    client = TelegramClient('umap_session', api_id, api_hash, 
                            system_version="Windows 10 x64", 
                            device_model="20S1S64W0X",
                            system_lang_code="ru-RU",
                            lang_code="en",
                            app_version="1.0.1a")
    client.start(phone)

    entity = client.get_entity(channel_or_chat)

    try:
        entity_name = entity.title
    except:
        entity_name = entity.username
        
    save_path = os.path.join(destination_directory, entity_name)
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    offset_id = 0
    counter = 0
    might_be_photos = True

    while might_be_photos:
        
        messages_iterator = client.iter_messages(entity=entity, limit=limit, offset_id=offset_id, filter=InputMessagesFilterPhotos)
        if not list(messages_iterator):
            break
        
        for message in messages_iterator:
            if start_date and message.date < start_date:
                print(f"Date {start_date_input} reached, exiting")
                might_be_photos = False
                break
                
            photos = message.media.photos if hasattr(message.media, 'photos') else [message.media.photo]
            for idx, photo in enumerate(photos):
                input_jpg_path = client.download_media(photo)

                date = message.date + time_delta
                date_str = date.strftime('%Y_%m_%d-%H_%M_%S')
                
                img_idx = 0 
                while True:
                    if img_idx == 0:
                        output_jpg_path = os.path.join(save_path, f"{date_str}.jpg")
                    else:
                        output_jpg_path = os.path.join(save_path, f"{date_str}-{img_idx}.jpg")
                
                    if os.path.exists(output_jpg_path):
                        img_idx += 1
                    else:
                        break

                exif_dict = piexif.load(input_jpg_path)
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date.strftime('%Y:%m:%d %H:%M:%S')
                exif_bytes = piexif.dump(exif_dict)

                with open(output_jpg_path, 'wb') as f:
                    with open(input_jpg_path, "rb") as original_file:
                        original_data = original_file.read()
                    f.write(original_data[:2])  # Write the JPEG SOI marker
                    f.write(exif_bytes)
                    f.write(original_data[2:])  # Write the rest of the original image data
                os.remove(input_jpg_path)
                    
                counter += 1
                print(f"{counter}/{messages_iterator.total}: {output_jpg_path.replace(f"{save_path}\\", '')}")
    
                time.sleep(delay)
                
            offset_id = message.id
                
    client.disconnect()

if __name__ == "__main__":
    api_id = input("Enter your API ID: ")
    api_hash = input("Enter your API Hash: ")
    phone = input("Enter your phone number: ")
    channel_or_chat = input("Enter the channel/chat name or ID: ")
    destination_directory = input("Enter the destination directory: ")
    start_date_input = input("Enter the start date (YYYY-MM-DD), leave empty if not needed: ")
    
    if start_date_input:
        start_date = datetime.strptime(start_date_input, '%Y-%m-%d').replace(tzinfo=timezone.utc) + time_delta
    else:
        start_date = None

    download_photos(api_id, api_hash, phone, channel_or_chat, destination_directory, limit=50, start_date=start_date)
