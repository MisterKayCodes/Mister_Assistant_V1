import os
import aiohttp
from datetime import datetime
from aiogram import Bot, types
from pathlib import Path

class MediaManager:
    def __init__(self, base_media_dir="data/media"):
        self.base_media_dir = base_media_dir
        os.makedirs(self.base_media_dir, exist_ok=True)

    async def save_photo(self, bot: Bot, photo: types.PhotoSize, user_id: str) -> str:
        """
        Downloads a photo and saves it to a structured folder.
        Returns the relative path starting from 'media/'.
        """
        now = datetime.now()
        # Structured Folder: data/media/12345/2026_03/
        sub_path = os.path.join(str(user_id), now.strftime("%Y_%m"))
        full_dir = os.path.join(self.base_media_dir, sub_path)
        os.makedirs(full_dir, exist_ok=True)

        file = await bot.get_file(photo.file_id)
        # Use file_id for unique naming, keep extension
        ext = os.path.splitext(file.file_path)[1] or ".jpg"
        filename = f"{photo.file_id}{ext}"
        
        full_path = os.path.join(full_dir, filename)
        
        # Download (Aiogram uses aiohttp internally)
        await bot.download_file(file.file_path, full_path)
        
        # Return relative path for DB (Rule 17: Environment Agnostic)
        # e.g. "media/123/2026_03/photo_id.jpg"
        return os.path.join("media", sub_path, filename).replace("\\", "/")

    async def cleanup_orphaned_media(self, repo):
        """
        The 'Janitor' logic: 
        1. Look at every file in data/media/
        2. Ask the Repository: 'Is this path known?'
        3. If 'No', delete the file.
        """
        media_root = Path(self.base_media_dir)
        if not media_root.exists():
            return

        print(f"[🧹] Starting Media Janitor in {self.base_media_dir}...")
        for file_path in media_root.rglob('*'):
            if file_path.is_file():
                # Convert to relative path e.g. "media/123/2026_03/photo.jpg"
                # Path relative to data/
                relative_path = os.path.join("media", file_path.relative_to(self.base_media_dir)).replace("\\", "/")
                
                if not repo.check_path_exists(relative_path):
                    try:
                        os.remove(file_path)
                        print(f"[🗑️] Deleted orphaned file: {relative_path}")
                    except Exception as e:
                        print(f"[🚨] Failed to delete {relative_path}: {e}")
        print("[🧹] Media Janitor finished.")
