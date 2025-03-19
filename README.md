

## Installation

### Installation on RPi (ARMv7)

Since there's no wheel for psycopg2, we need to install it from source. This will take a while.

```bash
sudo apt-get update
sudo apt-get install -y libpq-dev python3-dev

pip install wheel
pip install -r requirements.txt
```
