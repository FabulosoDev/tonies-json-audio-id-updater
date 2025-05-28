import asyncio
from dotenv import load_dotenv
from logger_factory import DefaultLoggerFactory
from teddycloud_api import TeddyCloudApi
from tonies_json_repo import ToniesJsonRepo
from yaml_updater import YamlUpdater

logger = DefaultLoggerFactory.get_logger(__name__)

load_dotenv()

teddycloud_api = TeddyCloudApi()
tonies_json_repo = ToniesJsonRepo()
yaml_updater = YamlUpdater()

async def get_new_tafs_with_infos():
    try:
        result_files = await teddycloud_api.get_library_files()
        if not result_files.get("success", False):
            error = result_files.get("error", "Unknown error")
            logger.error(f"Failed to get library: {error}")
            return None

        result_tags = await teddycloud_api.get_tonie_tags()
        if not result_tags.get("success", False):
            error = result_tags.get("error", "Unknown error")
            logger.error(f"Failed to get tags: {error}")
            return None

        files = result_files["files"]
        files_without_infos = [f for f in files if "tonieInfo" not in f]

        tags = result_tags["tags"]

        for file in files_without_infos:
            tag = next((t for t in tags if t.get("source", "").endswith(f'{file.get("name")}')), None)
            if tag and "tonieInfo" in tag:
                file["tonieInfo"] = tag["tonieInfo"]

        files_with_tonieinfo = [f for f in files_without_infos if "tonieInfo" in f]
        return files_with_tonieinfo

    except Exception as e:
        error = f"Error getting tonies: {str(e)}"
        logger.error(error)
        return None

def update_yamls(new_tafs_with_infos):
    if new_tafs_with_infos is None:
        return

    for taf_with_info in new_tafs_with_infos:
        model = taf_with_info.get("tonieInfo", {}).get("model", None)
        yaml_file_path = tonies_json_repo.find_yaml_by_model(model)
        if yaml_file_path:
            taf_header = taf_with_info.get("tafHeader", {})
            yaml_updater.update_yaml_by_taf_header(yaml_file_path, taf_header)

async def main():
    new_tafs_with_infos = await get_new_tafs_with_infos()
    update_yamls(new_tafs_with_infos)

if __name__ == "__main__":
    asyncio.run(main())