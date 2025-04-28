
import { useState } from 'react';
import { X } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (files: File[]) => void;
}

const UploadModal = ({ isOpen, onClose, onUpload }: UploadModalProps) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files) {
      const mediaFiles = Array.from(e.dataTransfer.files).filter(file => 
        file.type.startsWith('image/') || file.type.startsWith('video/')
      );
      
      setFiles(mediaFiles);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const mediaFiles = Array.from(e.target.files).filter(file => 
        file.type.startsWith('image/') || file.type.startsWith('video/')
      );
      
      setFiles(mediaFiles);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpload(files);
    setFiles([]);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-md">
        <div className="flex justify-between items-center border-b px-4 py-3">
          <h3 className="font-semibold text-lg">Upload Media</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-4">
          <div 
            className={`border-2 border-dashed rounded-lg p-8 text-center ${
              isDragging ? 'border-primary bg-blue-50' : 'border-gray-300'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input 
              type="file" 
              multiple 
              accept="image/*,video/*"
              onChange={handleFileSelect}
              className="hidden" 
              id="file-upload" 
            />
            
            {files.length > 0 ? (
              <div>
                <p className="mb-2 text-gray-700">
                  <span className="font-medium">{files.length}</span> {files.length === 1 ? 'file' : 'files'} selected
                </p>
                <ul className="text-left text-gray-700 text-sm max-h-32 overflow-y-auto">
                  {files.map((file, i) => (
                    <li key={i} className="truncate">{file.name}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <div>
                <p className="mb-2 text-gray-700">Drag and drop files here, or</p>
                <label 
                  htmlFor="file-upload"
                  className="cursor-pointer text-primary hover:text-primary-dark font-medium"
                >
                  Browse files
                </label>
              </div>
            )}
            
            <p className="mt-2 text-xs text-gray-500">Supported formats: JPG, PNG, GIF, MP4, MOV, etc.</p>
          </div>
          
          <div className="mt-4 flex justify-end">
            <button 
              type="button" 
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md mr-2"
            >
              Cancel
            </button>
            <button 
              type="submit"
              disabled={files.length === 0}
              className={`px-4 py-2 text-white rounded-md ${
                files.length === 0 ? 'bg-gray-400 cursor-not-allowed' : 'bg-primary hover:bg-primary/90'
              }`}
            >
              Upload
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UploadModal;
