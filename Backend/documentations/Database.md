```mermaid
// Users table - stores user information
Table users {
  id uuid [pk]
  email varchar(255) [unique, not null, note: 'User login email']
  fullname varchar(255) [note: 'User full name']
  password_hash text [not null, note: 'Hashed password']
  created_at timestamp [not null, default: `now()`, note: 'Account creation time']
  updated_at timestamp [not null, default: `now()`, note: 'Last update time']
  Indexes {
    email [name: "idx_users_email", type: "btree"]
  }
}

// Albums table - groups media items
Table albums {
  id uuid [pk]
  user_id uuid [not null, ref: > users.id, note: 'Owner of the album']
  title varchar(255) [not null, note: 'Album name']
  description text [note: 'Optional album description']
  created_at timestamp [not null, default: `now()`, note: 'Album creation time']
  updated_at timestamp [not null, default: `now()`, note: 'Last update time']
  Indexes {
    user_id [name: "idx_albums_user", type: "btree"]
  }
}

// Media table - core table for all media items (images, videos, etc.)
Table media {
  id uuid [pk]
  album_id uuid [ref: > albums.id, note: 'Optional album association']
  media_type varchar(10) [not null, note: 'e.g., "photo", "video", "audio", "document"']
  url text [not null, note: 'Storage location URL']
  file_size bigint [note: 'Size in bytes']
  created_at timestamp [not null, default: `now()`, note: 'Upload time']
  updated_at timestamp [not null, default: `now()`, note: 'Last update time']
  Indexes {
    album_id [name: "idx_media_album", type: "btree"]
    created_at [name: "idx_media_created", type: "btree"]
    (media_type, created_at) [name: "idx_media_type_created", type: "btree"]
  }
}

// Media Metadata table - technical details for media
Table media_metadata {
  id uuid [pk]
  media_id uuid [not null, ref: > media.id, unique, note: 'One-to-one with media']
  width int [note: 'Width in pixels']
  height int [note: 'Height in pixels']
  duration float [note: 'Duration in seconds (videos)']
  fps float [note: 'Frames per second (videos)']
  mime_type varchar(50) [note: 'MIME type, e.g., "image/jpeg"']
  resolution varchar(20) [note: 'e.g., "1920x1080"']
  gps_latitude decimal(10,8) [note: 'Latitude coordinate']
  gps_longitude decimal(11,8) [note: 'Longitude coordinate']
  capture_date timestamp [note: 'Original capture time']
  Indexes {
    media_id [name: "idx_metadata_media", type: "btree"]
  }
}

// Faces table - facial recognition data with avatar
Table faces {
  id uuid [pk]
  name varchar(100) [note: 'Identified face name, if known']
  avatar text [note: 'URL or path to avatar image']
  created_at timestamp [not null, default: `now()`, note: 'Face creation time']
}

// Face Embeddings table - stores multiple embeddings per face
Table face_embeddings {
  id uuid [pk]
  face_id uuid [not null, ref: > faces.id, note: 'Face this embedding belongs to']
  embedding_id uuid [not null, note: 'Qdrant embedding reference']
  created_at timestamp [not null, default: `now()`, note: 'Embedding creation time']
  Indexes {
    face_id [name: "idx_face_embeddings_face", type: "btree"]
    embedding_id [name: "idx_face_embeddings_embedding", type: "btree"]
  }
}

// Media-Faces junction table - links media to detected faces
Table media_faces {
  media_id uuid [not null, ref: > media.id, note: 'Media item containing the face']
  face_id uuid [not null, ref: > faces.id, note: 'Detected face']
  Indexes {
    (media_id, face_id) [pk]
    media_id [name: "idx_media_faces_media", type: "btree"]
    face_id [name: "idx_media_faces_face", type: "btree"]
  }
}

// Keyframes table - video keyframe references
Table keyframes {
  id uuid [pk]
  media_id uuid [not null, ref: > media.id, note: 'Parent video media']
  frame_idx int [not null, note: 'Frame index in video']
  created_at timestamp [not null, default: `now()`, note: 'Keyframe creation time']
  Indexes {
    media_id [name: "idx_keyframes_media", type: "btree"]
    (media_id, frame_idx) [name: "idx_keyframes_media_frame", type: "btree"]
  }
}

// Keyframe-Faces junction table - links keyframes to detected faces
Table keyframe_faces {
  keyframe_id uuid [not null, ref: > keyframes.id, note: 'Keyframe containing the face']
  face_id uuid [not null, ref: > faces.id, note: 'Detected face']
  Indexes {
    (keyframe_id, face_id) [pk]
    keyframe_id [name: "idx_keyframe_faces_keyframe", type: "btree"]
    face_id [name: "idx_keyframe_faces_face", type: "btree"]
  }
}

// Search History table - user search records
Table search_history {
  id uuid [pk]
  user_id uuid [not null, ref: > users.id]
  query text [not null, note: 'Search query string']
  executed_at timestamp [not null, default: `now()`, note: 'Search execution time']
  Indexes {
    user_id [name: "idx_search_user", type: "btree"]
    executed_at [name: "idx_search_time", type: "btree"]
    (user_id, executed_at) [name: "idx_search_user_time", type: "btree"]
  }
}

// Media Embeddings table - general content embedding references
Table media_embeddings {
  id uuid [pk]
  media_id uuid [not null, ref: > media.id, note: 'Media item']
  embedding_id uuid [not null, note: 'Qdrant embedding reference for media content']
  created_at timestamp [not null, default: `now()`, note: 'Embedding creation time']
  Indexes {
    media_id [name: "idx_embeddings_media", type: "btree"]
    embedding_id [name: "idx_embeddings_embedding", type: "btree"]
  }
}
```
