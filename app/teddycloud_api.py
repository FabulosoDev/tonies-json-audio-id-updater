from typing import Optional
import os
import time
import httpx
from logger_factory import DefaultLoggerFactory

logger = DefaultLoggerFactory.get_logger(__name__)

class TeddyCloudApi:
    def __init__(self):
        """Initialize TeddyCloudApi"""
        self.base_url = os.getenv("TEDDYCLOUD_API")
        if not self.base_url:
            logger.error("TEDDYCLOUD_API environment variable not set")
            raise ValueError("TEDDYCLOUD_API environment variable not set")

    async def get_library_files(self) -> dict:
        """Get library files from TeddyCloud"""
        url = f"{self.base_url}/api/fileIndexV2?path=/by/audioID&special=library"

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.debug(f"Fetching library files from TeddyCloud")
                response = await client.get(url)
                elapsed = time.time() - start_time
                logger.info(f"Request completed in {elapsed:.2f} seconds")
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Request failed after {elapsed:.2f} seconds: {str(e)}")
                return {"success": False, "error": f"External request failed: {str(e)}"}

            if response.status_code not in (200, 206):
                logger.error(f"Unexpected response code: {response.status_code}")
                return {"success": False, "error": f"Unexpected response code: {response.status_code}"}

            try:
                library = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                return {"success": False, "error": f"Failed to parse JSON: {str(e)}"}

            return {"success": True, "files": library.get("files", [])}

    async def get_tonie_tags(self) -> dict:
        """Get tonie tags from TeddyCloud"""
        url = f"{self.base_url}/api/getTagIndex"

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.debug(f"Fetching tonie tags from TeddyCloud")
                response = await client.get(url)
                elapsed = time.time() - start_time
                logger.info(f"Request completed in {elapsed:.2f} seconds")
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Request failed after {elapsed:.2f} seconds: {str(e)}")
                return {"success": False, "error": f"External request failed: {str(e)}"}

            if response.status_code not in (200, 206):
                logger.error(f"Unexpected response code: {response.status_code}")
                return {"success": False, "error": f"Unexpected response code: {response.status_code}"}

            try:
                tonies = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                return {"success": False, "error": f"Failed to parse JSON: {str(e)}"}

            return {"success": True, "tags": tonies.get("tags", [])}