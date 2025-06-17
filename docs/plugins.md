# Plugins

Plugin information is stored in the /config/plugins.yaml file.

The core service is responsible for managing this plugin list (loading, updating, deleting). The Web interface has a GUI to manage plugin configuration. Any changes there will be sent to the core service through the API.
</br></br>


## Configuration Structure

The **plugins.yaml** file contains a list of plugins. Here is the basic structure:

```yaml
- description: The Description of the plugin
  name: The name of the plugin
  webhook:
    allowed-ip:
    - 1.1.1.1
    auth-type: Authentication type
    secret: Secret/password
    url: Webhook URL
```

The order of the fields, and the order of the plugins in the list, are not important.
</br></br>


## Webhook Configuration

The webhook configuration controls how webhooks are handled.

The ***allowed-ip** area contains a list of IP's or networks that are authorised to send webhooks. This can be used as part of verifying that webhooks come from a legitimate source. This can be set to 0.0.0.0/0 to allow all.

The **auth_type** field is the type of authentication the webhook uses. This is another way of verifying the sender of the webhook. When authentication is used, an additional header is usually included with the webhook body, containing a signature of some sort.

Supported authentication methods are:
* none - No auth
* plain - Plain text password is included in a header
* basic - Basic username/password with Base64 encoding
* hash256 - HMAC with SHA256 hashing

The **secret** is the secret/password used with authentication. In the case of **basic** auth, this is the username and password as a string, separated by a colon. For example: username:password

The **url** is the path that webhooks are sent to. This is appended to '/plugin/<plugin-name>/'
</br></br>


## Plugin Management

Plugins are manages with the **PluginManagement** class in **plugins.py**.

Main methods:

| Method            | Usage                                                     |
| ----------------- | --------------------------------------------------------- |
| _validate_plugins | Validate that all fields are present in the plugin config |
| load_config       | Load config for each plugin                               |
| update_config     | Update the configuration for a plugin                     |
| register          | Register a new plugin                                     |
| delete            | Delete a plugin                                           |
