## Overview

This repository contains an implementation of an MQTT (Message Queuing Telemetry Transport) v3.1 server. MQTT is a lightweight, open messaging protocol designed for low-bandwidth, high-latency, or unreliable networks. This server provides a platform for facilitating communication between IoT devices.

## Features

- **MQTT Protocol Support**: Implements the MQTT v3.1 protocol, providing support for publish/subscribe messaging.
- **Retained Messages**: Retains the last message sent on a specific topic for new subscribers.
- **Last Will and Testament**: Allows clients to specify a "last will" message that will be sent if the client unexpectedly disconnects.
- **Session Persistence**: Optionally supports persistent sessions for clients, ensuring message delivery even if a client disconnects and reconnects.

## Getting Started

### Prerequisites

- Python 3.x
- other listed in `requirements.txt`

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com//MarcinZ20/MQTT-Server.git
    cd mqtt-server
    ```

2. Create a virtual environment (optional but recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the MQTT server:

    ```bash
    python main.py
    ```

## Configuration

- **Port**: The default MQTT port for unathenticated connection is 1883. Use 1884 for authenticated connetion, when `auth` is set to True.

## Usage

1. **Server setup**: Run the server using `python main.py`. Change the `auth` parameter if you want to use authenticated connection.
2. **Add authenticated users**: Add new users in the `config.py` for authenticated connection.
3. **Client Connection**: Use any MQTT client library or standalone client like MQTTX to connect to the server.

## Contributing

Contributions are welcome! Feel free to fork and create pull requests!

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
