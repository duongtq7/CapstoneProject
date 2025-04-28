import { useState } from "react";
import { UserPlus, Mail, Lock, User } from "lucide-react";
import { useToast } from "../../hooks/use-toast";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useAuth } from "../../hooks/useAuth";

const RegisterForm = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const { toast } = useToast();
  const { register, loading } = useAuth();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast({
        title: "Error",
        description: "Passwords do not match",
        variant: "destructive",
      });
      return;
    }

    if (password.length < 8) {
      toast({
        title: "Error",
        description: "Password must be at least 8 characters long",
        variant: "destructive",
      });
      return;
    }
    
    try {
      await register(email, password, name);
      
      toast({
        title: "Success",
        description: "Account created successfully",
      });
    } catch (error: any) {
      console.error("Registration error:", error);
      const errorMessage = error.response?.data?.detail || "Failed to create account. Please try again.";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  return (
    <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name" className="sr-only">Full Name</label>
        <div className="flex">
          <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
            <User className="h-5 w-5" />
          </span>
          <Input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            required
            className="rounded-l-none"
            placeholder="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
      </div>
      
      <div>
        <label htmlFor="email-address" className="sr-only">Email address</label>
        <div className="flex">
          <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
            <Mail className="h-5 w-5" />
          </span>
          <Input
            id="email-address"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="rounded-l-none"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
      </div>
      
      <div>
        <label htmlFor="password" className="sr-only">Password</label>
        <div className="flex">
          <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
            <Lock className="h-5 w-5" />
          </span>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            className="rounded-l-none"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
      </div>
      
      <div>
        <label htmlFor="confirm-password" className="sr-only">Confirm Password</label>
        <div className="flex">
          <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
            <Lock className="h-5 w-5" />
          </span>
          <Input
            id="confirm-password"
            name="confirm-password"
            type="password"
            autoComplete="new-password"
            required
            className="rounded-l-none"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </div>
      </div>

      <Button
        type="submit"
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <span className="absolute left-0 inset-y-0 flex items-center pl-3">
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </span>
        ) : (
          <span className="absolute left-0 inset-y-0 flex items-center pl-3">
            <UserPlus className="h-5 w-5 text-white" />
          </span>
        )}
        {loading ? "Creating account..." : "Create Account"}
      </Button>
    </form>
  );
};

export default RegisterForm;
