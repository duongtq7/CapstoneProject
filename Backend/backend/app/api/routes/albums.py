import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud
from app.api.deps import get_current_user, get_db
from app.models.album import AlbumCreate, AlbumResponse, AlbumUpdate
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(
    *,
    db: Session = Depends(get_db),
    album_in: AlbumCreate,
    current_user: User = Depends(get_current_user),
) -> AlbumResponse:
    """
    Create a new album for the current user.
    """
    album = crud.create_album(db=db, obj_in=album_in, user_id=current_user.id)
    return album


@router.get("/", response_model=list[AlbumResponse])
def read_albums(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> list[AlbumResponse]:
    """
    Retrieve all albums for the current user.
    """
    albums = crud.get_albums_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return albums


@router.get("/{album_id}", response_model=AlbumResponse)
def read_album(
    *,
    db: Session = Depends(get_db),
    album_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> AlbumResponse:
    """
    Get a specific album by ID.
    """
    album = crud.get_album(db=db, album_id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    if album.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return album


@router.put("/{album_id}", response_model=AlbumResponse)
def update_album(
    *,
    db: Session = Depends(get_db),
    album_id: uuid.UUID,
    album_in: AlbumUpdate,
    current_user: User = Depends(get_current_user),
) -> AlbumResponse:
    """
    Update an album.
    """
    album = crud.get_album(db=db, album_id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    if album.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    album = crud.update_album(db=db, db_obj=album, obj_in=album_in)
    return album


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(
    *,
    db: Session = Depends(get_db),
    album_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete an album.
    """
    album = crud.get_album(db=db, album_id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    if album.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    crud.delete_album(db=db, db_obj=album)
