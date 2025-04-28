export interface User {
  id: string;
  name: string;
  email: string;
}

export interface MediaItem {
  id: string;
  title: string;
  type: 'image' | 'video';
  url: string;
  presigned_url?: string;
  thumbnail?: string;
  description?: string;
  uploadDate: string;
  userId: string;
}
