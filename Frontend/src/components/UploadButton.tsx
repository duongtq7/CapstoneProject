
import { Upload } from 'lucide-react';

interface UploadButtonProps {
  onClick: () => void;
}

const UploadButton = ({ onClick }: UploadButtonProps) => {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 bg-primary text-white rounded-full p-3 shadow-lg hover:shadow-xl transition-all"
      aria-label="Upload Media"
    >
      <Upload className="w-6 h-6" />
    </button>
  );
};

export default UploadButton;
