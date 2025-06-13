"""
Module: plugins.py

Loads and manages plugin configurations for the core service.

Functions:
    - validate_ip_addresses(ip_addresses: list[str]) -> bool:
        Validates a list of IP addresses are in valid IP format.

Classes:
    - PluginConfig:
        Manages plugins; Add, configure, and delete plugins

Dependancies:
    - yaml: For reading and writing YAML configuration files.
    - urllib.parse: For URL encoding.
    - ipaddress: For validating IP addresses.
    - logging: For logging messages.

Custom Dependancies:
    - systemlog: For sending logs to the logging service.
"""


# Standard library imports
import yaml
import urllib.parse
from typing import Iterator
import logging
import ipaddress

# Custom imports
from systemlog import system_log


DEFAULT_PLUGIN_FILE = "config/plugins.yaml"


def validate_ip_addresses(
    ip_addresses: list[str]
) -> bool:
    """
    Validates a list of IP addresses.

    Args:
        ip_addresses (list[str]): List of IP addresses to validate.

    Returns:
        bool: True if all IP addresses are valid, False otherwise.
    """

    try:
        for address in ip_addresses:
            ipaddress.ip_address(address)
        return True

    except ValueError:
        return False


class PluginConfig:
    """
    Reads plugin configuration from a YAML file, and stores the values in
        instance variables

    Args:
        file_name (str): Path to the YAML configuration file.
    """

    def __init__(
        self,
        file_name=DEFAULT_PLUGIN_FILE,
    ) -> None:
        """
        Prepare the config dictionary and file path.

        Args:
            file_path (str): Path to the YAML configuration file.

        Returns:
            None
        """

        # Prepare the config
        self.plugin_file = file_name
        self.config = []

    def __len__(
        self
    ) -> int:
        """
        Magic method to get the length of the config list.

        Args:
            None

        Returns:
            int: The number of plugins in the config list.
        """

        return len(self.config)

    def __getitem__(
        self,
        index
    ) -> dict:
        """
        Magic method to get an item from the config list by index.

        Args:
            index (int): Index of the item to be retrieved.

        Returns:
            dict: The plugin configuration at the specified index.
        """

        return self.config[index]

    def __iter__(
        self
    ) -> Iterator[dict]:
        """
        Magic method to iterate over the config list.

        Args:
            None

        Returns:
            iter: An iterator over the config list.
        """

        return iter(self.config)

    def __contains__(
        self,
        name
    ) -> bool:
        """
        Magic method to check if a plugin name exists in the config list.

        Args:
            name (str): Name of the plugin to be checked.

        Returns:
            bool: True if the plugin name exists, False otherwise.
        """

        return any(entry['name'] == name for entry in self.config)

    def __repr__(
        self
    ) -> str:
        """
        Magic method to represent the PluginConfig object as a string.

        Args:
            None

        Returns:
            str: String representation of the PluginConfig object.
        """

        return f"<PluginConfig plugins={len(self.config)}>"

    def _validate_plugins(
        self
    ) -> None:
        """
        Validates that all required fields exist for each plugin.
            If there are invalid plugins, they are ignored.

        Args:
            None

        Returns:
            None
        """

        required_fields = ['name', 'description', 'webhook']
        webhook_fields = ['url', 'secret', 'allowed-ip']

        valid_plugins = []
        for idx, entry in enumerate(self.config):
            valid = True
            # Check top-level fields
            for field in required_fields:
                if field not in entry:
                    logging.error("Plugin at index %s", idx)
                    logging.error("Missing required field: %s", field)
                    valid = False

            # Check webhook subfields
            webhook = entry.get('webhook', {})
            for field in webhook_fields:
                if field not in webhook:
                    logging.error(
                        f"Plugin '{entry.get('name', '?')}' "
                        f"missing webhook field: {field}"
                    )
                    valid = False

            # Check allowed-ip is a list
            if (
                'allowed-ip' in webhook and
                not isinstance(webhook['allowed-ip'], list)
            ):
                logging.error(
                    f"Plugin '{entry.get('name', '?')}' "
                    f"webhook.allowed-ip must be a list"
                )
                valid = False

            if valid:
                valid_plugins.append(entry)
            else:
                logging.warning(
                    f"Removing invalid plugin entry: %s"
                    f"{entry.get('name', entry)}"
                )

        self.config = valid_plugins

    def load_config(
        self,
    ) -> None:
        """
        Loads the configuration from the YAML file.

        Reads the YAML file and initializes the instance variables.
        A list of dictionaries is created from the YAML file
            and stored in the instance variable `self.config`.
        Creates a unique route for each plugin by combining the plugin name
            and the webhook URL.

        Args:
            None

        Returns:
            None

        Raises:
            FileNotFoundError: If the configuration file is not found.
        """

        try:
            with open(self.plugin_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

        except FileNotFoundError:
            logging.error(
                "Configuration file not found: %s", self.plugin_file
            )
            raise FileNotFoundError(
                f"Configuration file not found: {self.plugin_file}"
            )

        # Validate the plugins
        self._validate_plugins()

        """
        Config format:

        [
            {
                "name": "<NAME>",
                "description": "<DESC>",
                "webhook": {
                    "url': "<URL>",
                    "secret": <SECRET>,
                    "allowed-ip": [
                        "<IP1>",
                        "<IP2>"
                    ]
                }
            },
            {...}
        ]
        """

        # Create the full webhook URL
        for entry in self.config:
            # Combine the plugin name and webhook URL to create a unique route
            safe_url = f"/plugin/{entry['name']}/{entry['webhook']['url']}"

            safe_url = safe_url.lower()

            # Handle spaces and special characters in the URL
            safe_url = safe_url.replace(" ", "_")
            safe_url = safe_url.replace("#", "")

            # Encode the URL to make it safe for use in a route
            entry['webhook']['safe_url'] = urllib.parse.quote(safe_url)

    def update_config(
        self,
        new_config: dict,
        plugin_config: str = DEFAULT_PLUGIN_FILE,
    ) -> bool:
        """
        Updates the configuration with a new list of dictionaries.

        Args:
            new_config (list): New configuration to be set.

        Returns:
            bool: True if the config updated successfully, False otherwise.

        new_config format:
        {
            "plugin_name": <ORIGINAL_NAME>,
            "name": "<NEW_NAME>",
            "description": "<DESCRIPTION>",
            "webhook": {
                "url': "<URL>",
                "secret": <SECRET>,
                "allowed-ip": [
                    "<IP1>",
                    "<IP2>"
                ]
        }
        """

        logging.info("Attempting to update config: %s", new_config)

        # Find existing entry in config
        for entry in self.config:
            if (entry['name']) == new_config['plugin_name']:
                # Update the entry with new values
                entry['name'] = (
                    new_config['name']
                )

                entry['description'] = (
                    new_config['description']
                )

                entry['webhook']['url'] = (
                    new_config['webhook']['url']
                )

                entry['webhook']['secret'] = (
                    new_config['webhook']['secret']
                )

                entry['webhook']['allowed-ip'] = (
                    new_config['webhook']['allowed-ip']
                )

                # Validate the allowed IP addresses
                if not validate_ip_addresses(
                    entry['webhook']['allowed-ip']
                ):
                    logging.error(
                        "Invalid IP addresses in allowed-ip: %s",
                        entry['webhook']['allowed-ip']
                    )
                    return False

                # Save the updated config back to the YAML file
                logging.info("Updated entry: %s", entry)

                try:
                    with open(
                        plugin_config,
                        "w",
                        encoding="utf-8"
                    ) as f:
                        yaml.dump(
                            self.config,
                            f,
                            default_flow_style=False,
                            allow_unicode=True
                        )
                except Exception as e:
                    logging.error("Failed to save config: %s", e)
                    return False

                # Send to logging service
                system_log.log(
                    f"Plugin '{entry['name']}' updated successfully."
                )

                return True

        # If no matching entry is found, return False
        logging.error(
            "Cannot update plugin. Entry %s not found",
            new_config['plugin_name']
        )
        return False

    def register(
        self,
        config: dict,
        plugin_config: str = DEFAULT_PLUGIN_FILE,
    ) -> bool:
        """
        Registers a new plugin by adding it to the configuration.

        Args:
            config (dict): Configuration for the new plugin.

        Returns:
            bool: True for successful registration, False otherwise.

        config format:
        {
            "name": "<PLUGIN_NAME>",
            "description": "<DESCRIPTION>",
            "webhook": {
                "url': "<URL>",
                "secret": <SECRET>,
                "allowed-ip": [
                    "<IP1>",
                    "<IP2>"
                ]
        }
        """

        logging.info("Attempting to register plugin: %s", config)

        # Check if the plugin already exists
        for entry in self.config:
            if entry['name'] == config['name']:
                logging.error("Plugin '%s' already exists.", config['name'])
                return False

        # Validate the allowed IP addresses
        if not validate_ip_addresses(config['webhook']['allowed-ip']):
            logging.error(
                "Invalid IP addresses in allowed-ip: %s",
                config['webhook']['allowed-ip']
            )
            return False

        # Create a new entry
        entry = {
            "name": config['name'],
            "description": config['description'],
            "webhook": {
                "url": config['webhook']['url'],
                "secret": config['webhook']['secret'],
                "allowed-ip": config['webhook']['allowed-ip']
            }
        }

        logging.info("New entry created: %s", entry)

        # Append the new entry to the existing config
        self.config.append(entry)
        logging.info("Current config: %s", self.config)

        # Save the updated config back to the YAML file
        try:
            with open(plugin_config, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )

        except Exception as e:
            logging.error("Failed to save config: %s", e)
            return False

        # Send to logging service
        system_log.log(f"Plugin '{config['name']}' registered successfully.")

        return True

    def delete(
        self,
        name: str,
        plugin_config: str = DEFAULT_PLUGIN_FILE,
    ) -> bool:
        """
        Deletes a plugin from the configuration.

        Args:
            name (str): Name of the plugin to be deleted.

        Returns:
            bool: True if the plugin was deleted successfully, False otherwise.
        """

        logging.warning(
            "Attempting to delete plugin: %s",
            name
        )

        # Find and remove the entry
        for entry in self.config:
            if entry['name'] == name:
                # Remove the entry from the list
                self.config.remove(entry)

                # Save the updated config back to the YAML file
                try:
                    with open(
                        plugin_config,
                        "w",
                        encoding="utf-8"
                    ) as f:
                        yaml.dump(
                            self.config,
                            f,
                            default_flow_style=False,
                            allow_unicode=True
                        )

                except Exception as e:
                    logging.error("Failed to save config: %s", e)
                    return False

                # Send to logging service
                system_log.log(
                    f"Plugin '{entry['name']}' deleted successfully."
                )

                return True

        # If no matching entry is found, return False
        logging.error("Cannot delete plugin. Entry %s not found", name)
        return False


if __name__ == "__main__":
    print("This module is not meant to be run directly.")
    print("Please run the main.py module instead.")
