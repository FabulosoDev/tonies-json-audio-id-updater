import os
from logger_factory import DefaultLoggerFactory
from git import Repo, GitCommandError
import yaml

logger = DefaultLoggerFactory.get_logger(__name__)

class ToniesJsonRepo:
    def __init__(self):
        """Initialize ToniesJsonRepo, optionally cloning/pulling a remote repo."""
        self.repo_url = os.getenv("TONIES_JSON_REPO_URL")
        if not self.repo_url:
            logger.error("TONIES_JSON_REPO_URL environment variable not set")
            raise ValueError("TONIES_JSON_REPO_URL environment variable not set")

        self.tonies_json_repo_path = os.getenv("TONIES_JSON_REPO_PATH")
        if not self.tonies_json_repo_path:
            logger.error("TONIES_JSON_REPO_PATH environment variable not set")
            raise ValueError("TONIES_JSON_REPO_PATH environment variable not set")

        self.tonies_json_update_branch = os.getenv("TONIES_JSON_UPDATE_BRANCH")
        if not self.tonies_json_update_branch:
            logger.error("TONIES_JSON_UPDATE_BRANCH environment variable not set")
            raise ValueError("TONIES_JSON_UPDATE_BRANCH environment variable not set")

        self._clone_or_pull_repo()

    def _clone_or_pull_repo(self):
        """Clone the repo if it doesn't exist, or pull the latest changes."""
        if not os.path.exists(self.tonies_json_repo_path):
            logger.info(f"Cloning repo {self.repo_url} to {self.tonies_json_repo_path}")
            Repo.clone_from(self.repo_url, self.tonies_json_repo_path)
        else:
            try:
                logger.info(f"Force resetting and pulling latest changes in {self.tonies_json_repo_path}")
                repo = Repo(self.tonies_json_repo_path)

                if repo.active_branch.name != "master":
                    repo.git.checkout("master")

                repo.remotes.origin.fetch()
                repo.git.reset('--hard', 'origin/master')
                repo.git.clean('-fd')

                remote_update_branch = f"origin/{self.tonies_json_update_branch}"
                if remote_update_branch in [ref.name for ref in repo.refs]:
                    repo.git.checkout('-B', self.tonies_json_update_branch, remote_update_branch)
                    repo.git.reset('--hard', remote_update_branch)
                else:
                    repo.git.checkout('-B', self.tonies_json_update_branch)

            except GitCommandError as e:
                logger.error(f"Failed to force pull repo: {e}")

    def _get_modified_yaml_files(self, repo):
        """Return a list of YAML files that are modified, staged, or untracked."""
        unstaged = repo.git.diff('--name-only').splitlines()
        staged = repo.git.diff('--cached', '--name-only').splitlines()
        untracked = repo.untracked_files

        all_changed = set(unstaged) | set(staged) | set(untracked)
        yaml_files = [f for f in all_changed if f.endswith('.yaml')]
        return yaml_files

    def _commit_file(self, repo, file_path):
        """Commit a single YAML file."""
        repo.git.add(file_path)
        commit_message = f"- add audio-id for {file_path}"

        if repo.is_dirty(path=file_path, untracked_files=True):
            repo.index.commit(commit_message)
            logger.info(f"Committed changes for {file_path}")
            return True
        return False

    def commit_changes(self):
        """Commit changes to YAML files, one commit per file."""
        repo = Repo(self.tonies_json_repo_path)

        if not repo.is_dirty(untracked_files=True):
            logger.info("No changes to commit.")
            return False

        git_username = os.getenv("GIT_USERNAME")
        git_email = os.getenv("GIT_EMAIL")

        if not (git_username and git_email):
            logger.warning("GIT_USERNAME or GIT_EMAIL not set. Skipping commit.")
            return False

        with repo.config_writer() as cw:
            cw.set_value("user", "name", git_username)
            cw.set_value("user", "email", git_email)

        yaml_files = self._get_modified_yaml_files(repo)

        committed = False
        for file_path in yaml_files:
            repo.git.reset()
            repo.git.add(file_path)
            if self._commit_file(repo, file_path):
                committed = True

        return committed

    def push_changes(self):
        """Push all committed changes to the remote repository."""
        repo = Repo(self.tonies_json_repo_path)
        git_username = os.getenv("GIT_USERNAME")
        git_token = os.getenv("GIT_TOKEN")

        if not (git_username and git_token):
            logger.warning("GIT_USERNAME or GIT_TOKEN not set. Skipping push.")
            return False

        try:
            # Set authenticated URL temporarily
            remote_url = self.repo_url.replace("https://", f"https://{git_username}:{git_token}@")
            with repo.remotes.origin.config_writer as cw:
                cw.set("url", remote_url)

            # Push changes
            repo.remotes.origin.push(
                refspec=f"{self.tonies_json_update_branch}:{self.tonies_json_update_branch}",
                force_with_lease=True
            )
            logger.info(f"Pushed all changes to branch {self.tonies_json_update_branch}")

            # Restore original URL
            with repo.remotes.origin.config_writer as cw:
                cw.set("url", self.repo_url)
            return True

        except GitCommandError as e:
            logger.error(f"Failed to push changes: {e}")
            return False

    def commit_and_push_changes(self):
        """Commit and push changes to the tonies-json repo."""
        if self.commit_changes():
            self.push_changes()

    def find_yaml_by_model(self, model):
        """Returns the found yaml file path for the given model."""
        if not model:
            return None
        yaml_path = os.path.join(self.tonies_json_repo_path, 'yaml')
        for root, _, files in os.walk(yaml_path):
            for file in files:
                if file == f"{model}.yaml":
                    logger.debug(f"Found yaml file for model {model}: {file}")
                    return os.path.join(root, file)
        return None