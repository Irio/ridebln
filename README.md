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

For now, it supports booking for a single ride per run. Also, it does not check if you already have a booking for the said ride.

## Development

```sh
isort --check .
black --check .
```

## Docker instructions

1. Run the Application:

```sh
docker compose up
```

2. Run linters:

```sh
docker compose run app sh -c "isort --check . && black --check ."
```

3. Access the App Container for Debugging:

```sh
docker compose run app sh
```

4. Stop All Services:

```sh
docker compose down
```
