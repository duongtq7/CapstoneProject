# Software Requirements Document (SRD)

## 1. Introduction

### 1.1 Purpose
The purpose of this document is to define the functional and non-functional requirements for a multimodal search system. The system allows users to upload media (images, videos) and perform searches using text (and optionally images). It processes uploaded media through AI models for embedding generation, face detection, face recognition, metadata extraction, and similarity search.

The system is designed for individuals and small teams to efficiently search and manage personal media collections using advanced AI capabilities. It can also extend to enterprise use cases, such as searching media within large communication channel groups.

### 1.2 Scope
The system enables users to:
- Upload images and videos.
- Process media to extract embeddings, metadata, and facial features.
- Search using text queries (image-based queries are a future consideration).
- Retrieve relevant media using similarity search and filtering.

The backend processes include:
- Vision-language model processing (CLIP, BLIP).
- Face detection followed by face recognition using PyTorch-based models.
- Metadata extraction from file metadata.
- Keyframe extraction for video processing.
- Query enhancement using spell correction and text segmentation (Vietnamese).
- Named Entity Recognition (NER) for filtering by location, human names, and time.
- Storage in MinIO (S3-compatible), Qdrant (vector database), and PostgreSQL.
- Authentication using OAuth and JWT.
- Error handling and rollback mechanisms for failed processing tasks.
- Ensuring real-time search capabilities.
- Hosting multimodal models on an inference server using Ray Serve for efficient, scalable processing.

**Exclusions:** The system does not support audio-only files or real-time video streaming analysis.
**Constraints:** Development timeline is 14 weeks; hardware and budget constraints are not specified but assumed to align with scalable cloud infrastructure.

## 2. User Roles & Permissions

### 2.1 Admin
- Manage users (create, update, delete, suspend accounts).
- View system statistics (e.g., total uploads, search frequency, error rates).
- No ability to override user actions (e.g., recover deleted media).

### 2.2 Regular User
- Upload media files (images and videos).
- Perform searches using text queries.
- View and manage personal media collection.
- No sharing of media or search results (out of scope).

## 3. System Features

### 3.1 Media Upload & Processing
- **Supported Formats:**
  - Images: JPEG, PNG, BMP (up to 10 MB per file).
  - Videos: MP4, AVI, MOV (up to 500 MB per file).
- **Processing:**
  - Extract embeddings using CLIP and BLIP models.
  - Extract face embeddings using PyTorch-based models.
  - Extract metadata (e.g., creation time, geolocation) from file properties.
  - Extract keyframes for videos (rate fully model-dependent, optimized by the model).
- **Error Handling:**
  - Corrupted files are rejected with an error message displayed in the UI.
  - Unsupported formats trigger a user notification via UI.

### 3.2 Search Mechanism
- **Query Input:** Users search using text queries (e.g., "A group of friends had dinner in Hanoi last year."); image-based queries are a future nice-to-have feature.
- **Performance:** Search results return within 2 seconds for 90% of queries.
- **Query Enhancement Includes:**
  - Spell correction (e.g., "Hanoii" → "Hanoi").
  - Text segmentation for Vietnamese (e.g., "Tôi yêu Việt Nam" → ["Tôi", "yêu", "Việt_Nam"]).
- **Named Entity Recognition (NER):** Used to extract relevant details such as:
  - Locations (e.g., "Hanoi").
  - Names (e.g., "Ho Huu Tuong").
  - Temporal references (e.g., "2023-05-01" or "last year").

To refine search results, the system provides the following filtering options:
- Date range (e.g., "Jan 2023 - Dec 2023").
- Location-based filtering.
- Face matching (targeting 95% accuracy).

The system processes search queries through the following steps:
1. Query expansion to improve relevance and recall.
2. Multimodal embedding extraction, where the query is converted into an embedding representation.
3. Similarity search, using cosine similarity to find the most relevant media.
4. Named Entity Recognition (NER) to extract structured information such as places, human names, and time references.
5. Filtering mechanisms, including date range, location-based filtering, and face matching.
6. Dynamic ranking, which sorts results based on similarity scores to prioritize the most relevant media.

### 3.3 Data Storage
- **Vector Database (Qdrant):**
  - Stores embeddings for images and videos.
  - Supports similarity search using cosine similarity.
  - Embedding dimensions and similarity thresholds will be defined per model.
- **PostgreSQL Database:**
  - Stores users, albums, faces, media metadata.
  - Schema includes:
    - Users table.
    - Albums table (each user has exactly one album).
    - Faces table (one face can appear in multiple media items).
    - Media table (storing media metadata and relationships).
    - Media_Album table (associating media files with the user’s album).
    - Media_Face table (linking detected faces with multiple media items).
    - Search_History table (logging user search queries and results).
    - Processing_Logs table (tracking media processing stages and errors).
    - Media_Annotations table (storing additional metadata or AI-generated labels on media files).
- **MinIO (S3-compatible Storage):**
  - Stores media files.
  - Organized using the following structure: `/users/{user_id}/albums/{album_id}/{media_id}.{extension}`
  - **Deletion Policy:** Files are only deleted when the user manually removes them or the account is deleted.
  - **Bucket Policies:**
    - Media files stored in MinIO will have private access by default.
  - **Data Encryption:**
    - AES-256 encryption for data at rest.
    - SSL/TLS encryption for data in transit.
  - **Access Control:**
    - Only authorized users can upload/delete their media.
    - Admins can audit but not modify user data.

### 3.4 Authentication & Security
- **Authentication:** Google OAuth with JWT (tokens expire after 24 hours).
- **Security Measures:**
  - Rate limiting: 10 requests per minute per user.
  - Secure token storage (hashed in PostgreSQL).
  - Role-based access control (RBAC).
  - Encryption: AES-256 at rest, SSL/TLS in transit.
  - Logging for security events (e.g., failed logins).
- **Additional Security Measures:**
  - GDPR/CCPA best practices: Users can request data deletion; consent required for OAuth.
  - Admins can audit but not modify user data.

### 3.5 Error Handling & Rollback
- **Rollback Triggers:** Storage, database, inference server, or embedding generation failures.
  - Storage failure (MinIO unreachable).
  - Database failure (PostgreSQL unreachable).
  - Inference server failure.
  - Embedding generation failure.
  - Additional failure cases as identified.
- **Retry Mechanism:** Up to 3 retries for failed processing; users notified via UI/email if all retries fail, requiring re-upload.
- **Partial Uploads:** Users must restart incomplete uploads.

## 4. Scalability & Performance
- **Initial Scale:** 100 users.
- **Real-Time:** Search queries prioritized over uploads under load; uploads queued as needed.
- **Designed for horizontal scaling:** (e.g., Ray Serve nodes).

## 5. External API Integrations
- Potential APIs for geolocation, NER, and other enhancements.
- Specific integrations to be determined based on implementation needs.

## 6. Future Considerations
- Support for image-based queries if feasible within the development timeline.
- Optimization of storage and retrieval mechanisms.
- Expanding user roles and permissions as needed.

## 7. Conclusion
This document outlines the functional and non-functional requirements for the multimodal search system. Further refinements will be made during implementation as necessary.
