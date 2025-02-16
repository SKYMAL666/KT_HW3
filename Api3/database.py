from sqlmodel import SQLModel, create_engine, Session
from models import FileInfo

# Настройка подключения к базе данных
DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/media_db"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session

def save_file_to_db(file_id: str, file_type: str, file_size: int, file_path: str):
    with Session(engine) as session:
        file_info = FileInfo(
            id=file_id,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
        )
        session.add(file_info)
        session.commit()
        session.refresh(file_info)

def get_files_from_db():
    with Session(engine) as session:
        files = session.query(FileInfo).all()
        return [
            {
                "id": file.id,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "file_path": file.file_path,
                "upload_time": file.upload_time,
            }
            for file in files
        ]