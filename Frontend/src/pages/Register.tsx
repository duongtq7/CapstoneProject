
import { Link } from "react-router-dom";
import RegisterForm from "@/components/auth/RegisterForm";
import GoogleSignUpButton from "@/components/auth/GoogleSignUpButton";

const Register = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="mt-6 text-center text-3xl font-extrabold text-gray-900">Glimpse</h1>
          <h2 className="mt-2 text-center text-lg font-medium text-gray-600">Create your account</h2>
        </div>
        
        <RegisterForm />
        
        <div className="flex items-center justify-center">
          <div className="text-sm">
            <Link to="/login" className="font-medium text-primary hover:text-primary/90">
              Already have an account? Sign in
            </Link>
          </div>
        </div>
        
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">Or continue with</span>
            </div>
          </div>

          <div className="mt-6">
            <GoogleSignUpButton />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
