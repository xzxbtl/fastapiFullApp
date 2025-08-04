from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv, find_dotenv

env_file_path = find_dotenv('../venv/__base_conf__.env')


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    model_config = SettingsConfigDict(env_file=env_file_path, env_file_encoding='utf-8')

    @property
    def DataBase_URL_psycopg(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


load_dotenv()
settings = Settings()
