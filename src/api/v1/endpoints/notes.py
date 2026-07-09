"""
Notes CRUD endpoints — demonstrates database usage via dependency injection.

Every route receives a DBSession through FastAPI's Depends() system,
which handles commit/rollback/close automatically.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.api.deps import DBSession
from src.db.models.note import Note
from src.schemas.note import NoteCreate, NoteRead

router = APIRouter()


@router.get("", response_model=list[NoteRead])
async def list_notes(db: DBSession):
    """Return all notes, newest first."""
    result = await db.execute(select(Note).order_by(Note.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(body: NoteCreate, db: DBSession):
    """Create a new note and persist it to the database."""
    note = Note(title=body.title, content=body.content)
    db.add(note)
    await db.flush()  # populates note.id before commit
    await db.refresh(note)
    return note


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(note_id: int, db: DBSession):
    """Fetch a single note by primary key."""
    note = await db.get(Note, note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
    return note
