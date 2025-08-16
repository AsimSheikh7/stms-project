export interface User {
  email: string;
  role: string;
}

export interface AuthResponse {
  token: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}
