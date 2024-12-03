# Ridebln

## Setup

1. Install the dependencies:
    
    ```sh
    pip3 install -r requirements.txt
    ```

2. Create your configuration file and change it according to your preferences:

    ```sh
    cp settings.toml.example settings.toml
    ```

## Usage

**Be aware that running this software may incur costs.**

Run the script to book a ride according to your preferences:

```sh
python3 main.py
```

For now, it supports booking for a single ride per run.

## Development

```sh
isort --check .
black --check .
```
