import yaml
from logger_factory import DefaultLoggerFactory

logger = DefaultLoggerFactory.get_logger(__name__)

class YamlUpdater:
    def update_yaml_by_taf_header(self, yaml_file_path, taf_header):
        if not yaml_file_path or not taf_header or not taf_header.get("valid", False):
            return

        with open(yaml_file_path, 'r', encoding='utf-8') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        yaml_id_data = {
            "audio-id": taf_header.get("audioId"),
            "hash": taf_header.get("sha1Hash"),
            "size": taf_header.get("size"),
            "tracks": len(taf_header.get("trackSeconds", [])),
            "confidence": 0,
        }

        if yaml_id_data["audio-id"] is not None and yaml_id_data["hash"] is not None:
            for entry in yaml_data.get("data", []):
                if "ids" in entry:
                    already_present = any(
                        i.get("audio-id") == yaml_id_data["audio-id"] and i.get("hash") == yaml_id_data["hash"]
                        for i in entry["ids"]
                    )
                    if not already_present:
                        entry["ids"].insert(0, yaml_id_data)

                        # Write YAML back only if a new id was added
                        with open(yaml_file_path, 'w', encoding='utf-8') as yaml_file:
                            yaml.dump(yaml_data, yaml_file, allow_unicode=True, sort_keys=False)
                            logger.info(f"Updated YAML file: {yaml_file_path}")
                        return

                    else:
                        logger.warning(f"Id already present in {yaml_file_path}, skipping write.")
