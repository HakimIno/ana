from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column
from datetime import datetime, timezone
from config import settings
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20)) # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ChatMemory:
    """Manages persistent chat history using SQLite."""
    
    def __init__(self, db_path=None):
        if not db_path:
            db_path = str(settings.BASE_DIR / "chat_memory.db")
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the persistent store."""
        session = self.Session()
        try:
            msg = ChatMessage(session_id=session_id, role=role, content=content)
            session.add(msg)
            session.commit()
            logger.info(f"Saved {role} message to session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
        finally:
            session.close()

    def get_history(self, session_id: str, limit: int = 10) -> list:
        """Retrieve recent chat history for a session."""
        session = self.Session()
        try:
            messages = session.query(ChatMessage)\
                .filter(ChatMessage.session_id == session_id)\
                .order_by(ChatMessage.timestamp.desc())\
                .limit(limit)\
                .all()
            
            logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
            
            # Return in chronological order
            return [{"role": m.role, "content": m.content} for m in reversed(messages)]
        finally:
            session.close()

    def clear_history(self, session_id: str):
        """Clear history for a specific session."""
        session = self.Session()
        try:
            session.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            session.commit()
        finally:
            session.close()
