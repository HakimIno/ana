from sqlalchemy import create_engine, Text, DateTime, text, String
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column
from datetime import datetime, timezone
from typing import Optional, Dict
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
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON blob for rich data
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ChatMemory:
    """Manages persistent chat history using SQLite."""
    
    def __init__(self, db_path=None):
        if not db_path:
            db_path = str(settings.BASE_DIR / "chat_memory.db")
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        # Enable WAL mode for better performance and concurrency
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_message(self, session_id: str, role: str, content: str, data: Optional[Dict] = None):
        """Add a message to the persistent store."""
        import json
        session = self.Session()
        try:
            data_json = json.dumps(data) if data else None
            msg = ChatMessage(session_id=session_id, role=role, content=content, data=data_json)
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
            
            import json
            # Return in chronological order
            formatted = []
            for m in reversed(messages):
                msg_dict = {"role": m.role, "content": m.content}
                if m.data:
                    try:
                        msg_dict["data"] = json.loads(m.data)
                    except Exception:
                        msg_dict["data"] = None
                formatted.append(msg_dict)
            return formatted
        finally:
            session.close()

    def list_sessions(self) -> list:
        """List all unique session IDs with their last message timestamp."""
        from sqlalchemy import func
        session = self.Session()
        try:
            # Get unique session_ids and their latest timestamp
            results = session.query(
                ChatMessage.session_id,
                func.max(ChatMessage.timestamp).label('last_active')
            ).group_by(ChatMessage.session_id).order_by(func.max(ChatMessage.timestamp).desc()).all()
            
            return [{"session_id": r.session_id, "last_active": r.last_active} for r in results]
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
