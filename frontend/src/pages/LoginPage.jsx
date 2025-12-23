import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ScaleIcon, EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";
import { useAuthStore } from "../store/authStore";
import toast from "react-hot-toast";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email || !password) {
      toast.error("Email va parolni kiriting");
      return;
    }

    const result = await login(email, password);

    if (result.success) {
      toast.success("Muvaffaqiyatli kirildi!");
      navigate("/dashboard");
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-blue-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="flex items-center">
              <ScaleIcon className="h-12 w-12 text-primary-600" />
              <span className="ml-3 text-3xl font-bold text-gray-900">
                Legal Bridge AI
              </span>
            </div>
          </div>
          <h2 className="mt-6 text-center text-xl font-semibold text-gray-600">
            Shartnomalar tahlili tizimi
          </h2>
          <p className="mt-2 text-center text-sm text-gray-500">
            O'zbekiston qonunchiligiga muvofiqlikni tekshirish
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email manzil
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field"
                  placeholder="sizning@email.uz"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Parol
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pr-12"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-primary-600 transition-colors duration-200"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" aria-hidden="true" />
                  ) : (
                    <EyeIcon className="h-5 w-5" aria-hidden="true" />
                  )}
                  <span className="sr-only">
                    {showPassword ? "Parolni yashirish" : "Parolni ko'rish"}
                  </span>
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="remember-me"
                  className="ml-2 block text-sm text-gray-900"
                >
                  Eslab qolish
                </label>
              </div>

              <div className="text-sm">
                <a
                  href="/forgot-password"
                  className="font-medium text-primary-600 hover:text-primary-500"
                >
                  Parolni unutdingizmi?
                </a>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary py-3 text-base"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Kirish...
                  </span>
                ) : (
                  "Kirish"
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Hisobingiz yo'qmi?{" "}
              <a
                href="/register"
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                Ro'yxatdan o'ting
              </a>
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-gray-500 mt-4">
          © 2025 Legal Bridge AI. Barcha huquqlar himoyalangan.
        </p>
      </div>
    </div>
  );
}
