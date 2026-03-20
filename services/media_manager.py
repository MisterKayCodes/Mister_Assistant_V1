import os
import logging
from datetime import datetime
from pathlib import Path
from aiogram import Bot, types

# Shared logger (Rule 10: Observability)
logger = logging.getLogger(__name__)

class MediaManager:
    def __init__(self, base_media_dir="data/media"):
        # Rule 17: Environment Agnostic / Absolute Internal Paths
        self.base_media_dir = Path(base_media_dir).resolve()
        self.base_media_dir.mkdir(parents=True, exist_ok=True)

    async def save_photo(self, bot: Bot, photo: types.PhotoSize, user_id: str) -> str:
        """
        Downloads a photo and saves it to a structured folder.
        Returns the relative path starting from 'media/' for DB storage.
        """
        now = datetime.now()
        # Structure: media/user_id/YYYY_MM/
        sub_path = Path(str(user_id)) / now.strftime("%Y_%m")
        full_dir = self.base_media_dir / sub_path
        full_dir.mkdir(parents=True, exist_ok=True)

        file = await bot.get_file(photo.file_id)
        # Use file_id for unique naming, keep extension
        ext = os.path.splitext(file.file_path)[1] or ".jpg"
        filename = f"{photo.file_id}{ext}"
        
        full_path = full_dir / filename
        
        # Download (Aiogram uses aiohttp internally)
        await bot.download_file(file.file_path, full_path)
        
        # Consistent Path Contract: 'media/user_id/date/file.jpg'
        # Rule 5: .as_posix() forces forward slashes (Compatible with Win/Linux DB storage)
        relative_db_path = (Path("media") / sub_path / filename).as_posix()
        return relative_db_path

    async def cleanup_orphaned_media(self, repo):
        """
        The 'Janitor' logic (Rule 14: Data Minimization): 
        1. Look at every file in data/media/
        2. Ask the Repository: 'Is this path known?'
        3. If 'No', delete the file.
        """
        if not self.base_media_dir.exists():
            return

        logger.info(f"🧹 Media Janitor starting in {self.base_media_dir}")
        files_deleted = 0
        
        for file_path in self.base_media_dir.rglob('*'):
            if file_path.is_file():
                # Reconstruct the DB key by taking everything after 'data'
                # e.g. 'media/123/2026_03/abc.jpg'
                relative_to_data = file_path.relative_to(self.base_media_dir.parent)
                db_key = relative_to_data.as_posix()
                
                if not repo.check_path_exists(db_key):
                    try:
                        os.remove(file_path)
                        logger.warning(f"🗑️ Deleted orphaned file: {db_key}")
                        files_deleted += 1
                    except Exception as e:
                        logger.error(f"🚨 Failed to delete {db_key}: {e}")
                        
        logger.info(f"🧹 Janitor finished. Removed {files_deleted} files.")
