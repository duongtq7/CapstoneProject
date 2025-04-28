import { Link, useLocation } from "react-router-dom";
import { Home, Search, Settings, LogOut } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const Navbar = () => {
  const location = useLocation();
  const { logout } = useAuth();
  
  const isActive = (path: string) => {
    return location.pathname === path;
  };
  
  return (
    <header className="w-full border-b border-gray-200">
      <div className="flex justify-between items-center py-3 px-4 max-w-7xl mx-auto">
        <div className="flex-shrink-0">
          <Link to="/" className="font-bold text-xl">Glimpse</Link>
        </div>
        
        <div className="flex items-center space-x-2">
          <Link 
            to="/" 
            className={`flex items-center rounded-lg px-3 py-2 transition-colors ${
              isActive("/") 
                ? "bg-primary text-white" 
                : "hover:bg-gray-100"
            }`}
          >
            <Home className="w-5 h-5 mr-1" />
            <span>Home</span>
          </Link>
          
          <Link 
            to="/search" 
            className={`flex items-center rounded-lg px-3 py-2 transition-colors ${
              isActive("/search") 
                ? "bg-primary text-white" 
                : "hover:bg-gray-100"
            }`}
          >
            <Search className="w-5 h-5 mr-1" />
            <span>Search</span>
          </Link>
          
          <Link 
            to="/settings" 
            className={`flex items-center rounded-lg px-3 py-2 transition-colors ${
              isActive("/settings") 
                ? "bg-primary text-white" 
                : "hover:bg-gray-100"
            }`}
          >
            <Settings className="w-5 h-5 mr-1" />
            <span>Settings</span>
          </Link>
          
          <button 
            onClick={logout}
            className="flex items-center rounded-lg px-3 py-2 text-gray-700 hover:bg-gray-100 transition-colors"
            aria-label="Logout"
            type="button"
          >
            <LogOut className="w-5 h-5 mr-1" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
