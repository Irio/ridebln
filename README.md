# Ridebln

## Setup

```sh
pip3 install -r requirements.txt
```

## Usage

**Be aware that running this software may incur costs.**

1. Create your configuration file and change it according to your preferences:
    ```sh
    cp settings.toml.example settings.toml
    ```
2. Trigger the bookings.
    ```sh
    python3 main.py
    ```


## Development

```sh
isort --check .
black --check .
```
