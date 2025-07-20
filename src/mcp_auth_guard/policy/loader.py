"""Policy loader for loading policies from YAML files."""

import logging
from pathlib import Path

import yaml

from ..schemas.policy import PolicyConfig

logger = logging.getLogger(__name__)


class PolicyLoader:
    """Loads policies from YAML files or dictionaries."""

    @staticmethod
    def load_from_file(file_path: str | Path) -> PolicyConfig:
        """
        Load a single policy from a YAML file.

        Args:
            file_path: Path to the YAML policy file

        Returns:
            PolicyConfig object
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Validate and parse the policy
            if isinstance(data.get("default_effect"), str):
                from ..schemas.policy import Effect

                data["default_effect"] = Effect(data["default_effect"].lower())
            policy = PolicyConfig.model_validate(data)

            logger.info(f"Loaded policy '{policy.name}' from {file_path}")
            return policy

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading policy from {file_path}: {e}")

    @staticmethod
    def load_from_directory(directory: str | Path) -> list[PolicyConfig]:
        """
        Load all policies from YAML files in a directory.

        Args:
            directory: Directory containing YAML policy files

        Returns:
            List of PolicyConfig objects
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        policies = []
        yaml_files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))

        for file_path in yaml_files:
            try:
                policy = PolicyLoader.load_from_file(file_path)
                policies.append(policy)
            except Exception as e:
                logger.error(f"Failed to load policy from {file_path}: {e}")
                # Continue loading other files

        logger.info(f"Loaded {len(policies)} policies from {directory}")
        return policies

    @staticmethod
    def load_from_dict(data: dict) -> PolicyConfig:
        """
        Load a policy from a dictionary.

        Args:
            data: Policy data as a dictionary

        Returns:
            PolicyConfig object
        """
        try:
            if isinstance(data.get("default_effect"), str):
                from ..schemas.policy import Effect

                data["default_effect"] = Effect(data["default_effect"].lower())
            policy = PolicyConfig.model_validate(data)
            logger.debug(f"Loaded policy '{policy.name}' from dictionary")
            return policy
        except Exception as e:
            raise ValueError(f"Error loading policy from dictionary: {e}")

    @staticmethod
    def validate_policy_file(file_path: str | Path) -> bool:
        """
        Validate a policy YAML file without loading it.

        Args:
            file_path: Path to the YAML policy file

        Returns:
            True if valid, False otherwise
        """
        try:
            PolicyLoader.load_from_file(file_path)
            return True
        except Exception as e:
            logger.error(f"Policy validation failed for {file_path}: {e}")
            return False

    @staticmethod
    def save_to_file(policy: PolicyConfig, file_path: str | Path):
        """
        Save a policy to a YAML file.

        Args:
            policy: PolicyConfig to save
            file_path: Output file path
        """
        file_path = Path(file_path)

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert to dict and save as YAML
            data = policy.model_dump(exclude_none=True)

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=2,
                )

            logger.info(f"Saved policy '{policy.name}' to {file_path}")

        except Exception as e:
            raise ValueError(f"Error saving policy to {file_path}: {e}")
