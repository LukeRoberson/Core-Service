"""
Module: config.py

Loads and manages global configuration for the core service.

Classes:
    - GlobalConfig:
        Manage global app configuration

Dependancies:
    - yaml: For reading and writing YAML configuration files.
    - logging: For logging messages.
"""

# Standard library imports
import yaml
import logging


DEFAULT_CONFIG_FILE = "config/global.yaml"


class GlobalConfig:
    """
    Reads global configuration from a YAML file, and stores the values
        in instance variables

    Args:
        file_name (str): Path to the YAML configuration file.
    """

    def __init__(
        self,
        file_name: str = DEFAULT_CONFIG_FILE,
    ) -> None:
        """
        Prepare the config dictionary and file path.

        Args:
            file_path (str): Path to the YAML configuration file.

        Returns:
            None
        """

        # Prepare the config
        logging.info("Initializing GlobalConfig with file: %s", file_name)
        self.config_file = file_name
        self.config = {}

    def __repr__(
        self
    ) -> str:
        """
        Magic method to represent the GlobalConfig object as a string.

        Args:
            None

        Returns:
            str: String representation of the GlobalConfig object.
        """

        return f"<GlobalConfig sections={list(self.config.keys())}>"

    def __str__(
        self
    ) -> str:
        """
        Magic method to convert the GlobalConfig object to a string.

        Args:
            None

        Returns:
            str: String representation of the GlobalConfig object.
        """

        return str(self.config)

    def _validate_sections(
        self,
        config: dict,
        section_requirements: dict,
    ) -> None:
        """
        Helper function to validate required sections and keys in the config.

        Args:
            config (dict): The loaded configuration dictionary.
            section_requirements (dict): Keys are section names,
                values are lists of required keys.

        Returns:
            None

        Raises:
            ValueError: If a required section or key is missing.
        """

        # Check for required sections and keys
        for section, required_keys in section_requirements.items():
            # Check if the section exists in the config
            if section not in config:
                logging.critical(f"Missing '{section}' in configuration.")
                raise ValueError(
                    f"Missing '{section}' in configuration."
                )

            # Check if the required keys exist in the section
            if required_keys:
                for key in required_keys:
                    if key not in config[section]:
                        logging.critical(f"Missing '{key}' in '{section}'")

        # Check logging level is valid
        valid_levels = {"debug", "info", "warning", "error", "critical"}
        level = config.get("web", {}).get("logging-level", "").lower()
        if level not in valid_levels:
            logging.error(f"Invalid logging-level '{level}'")

    def load_config(
        self,
    ) -> None:
        """
        Loads the configuration from the YAML file.

        Reads the YAML file and initializes the instance variables.
        A list of dictionaries is created from the YAML file
            and stored in the instance variable 'self.config'.
        Validates the config by checking for required sections and keys.

        Args:
            None

        Returns:
            None

        Raises:
            FileNotFoundError: If the configuration file is not found.
            ValueError: If a required section or key is missing.
        """

        # Read the YAML file
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

        except FileNotFoundError:
            logging.error(
                "Configuration file not found: %s", self.config_file
            )
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}"
            )

        # Define required sections and their required keys
        section_requirements = {
            "azure": ["tenant-id"],
            "authentication": [
                "app-id", "app-secret", "salt", "redirect-uri", "admin-group"
            ],
            "teams": [
                "app-id", "app-secret", "salt", "user",
                "public-key", "private-key"
            ],
            "sql": [
                "server", "port", "database", "username", "password", "salt"
            ],
            "web": ["logging-level"]
        }

        # Validate the config
        self._validate_sections(self.config, section_requirements)

    def update_config(
        self,
        config: dict,
    ) -> bool:
        """
        Updates the configuration with a new dictionary.
        Only the main section is passed from the UI.

        Args:
            config (dict): New configuration to be set.

        Returns:
            bool: True if the config updated successfully, False otherwise.
        """

        logging.info("Saving global config: %s", config)

        # Azure Section
        if config['category'] == "azure":
            self.config['azure']['tenant-id'] = (
                config['tenant_id']
            )

        # Authentication Section
        elif config['category'] == "authentication":
            self.config['authentication']['app-id'] = (
                config['auth_app_id']
            )
            self.config['authentication']['app-secret'] = (
                config['auth_app_secret']
            )
            self.config['authentication']['salt'] = (
                config['auth_salt']
            )
            self.config['authentication']['redirect-uri'] = (
                config['auth_redirect_uri']
            )
            self.config['authentication']['admin-group'] = (
                config['auth_admin_group']
            )

        # Teams Section
        elif config['category'] == "teams":
            self.config['teams']['app-id'] = (
                config['teams_app_id']
            )
            self.config['teams']['app-secret'] = (
                config['teams_app_secret']
            )
            self.config['teams']['salt'] = (
                config['teams_salt']
            )
            self.config['teams']['user'] = (
                config['teams_user_name']
            )
            self.config['teams']['public-key'] = (
                config['teams_public_key']
            )
            self.config['teams']['private-key'] = (
                config['teams_private_key']
            )

        # SQL Section
        elif config['category'] == "sql":
            self.config['sql']['server'] = (
                config['sql_server']
            )
            self.config['sql']['port'] = (
                config['sql_port']
            )
            self.config['sql']['database'] = (
                config['sql_database']
            )
            self.config['sql']['username'] = (
                config['sql_username']
            )
            self.config['sql']['password'] = (
                config['sql_password']
            )
            self.config['sql']['salt'] = (
                config['sql_salt']
            )

        # Web Section
        elif config['category'] == "web":
            self.config['web']['logging-level'] = (
                config['web_logging_level'].lower()
            )

        # If the category is not recognized, return False
        else:
            logging.error(
                "Config update: Invalid category: %s", config['category']
            )
            return False

        # Save the updated config back to the YAML file
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )

        except Exception as e:
            logging.error("Failed to save config: %s", e)
            return False

        return True


if __name__ == "__main__":
    print("This module is not meant to be run directly.")
    print("Please run the main.py module instead.")
