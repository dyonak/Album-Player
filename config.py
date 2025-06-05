import json

class Config:
    _instance = None

    def __new__(cls, config_file="./config.json"):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config(config_file)
        return cls._instance

    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                for key, value in config_data.items():
                    setattr(self, key, value)
        except FileNotFoundError:
            print(f"Error: config file '{config_file}' not found.")
        except json.JSONDecodeError:
            print(f"Error: invalid JSON format in '{config_file}'.")
    
    def reload(self, config_file="config.json"):
        self.load_config(config_file)


if __name__ == "__main__":
  config = Config()
  print(config.port)