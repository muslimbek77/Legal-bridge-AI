import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ScaleIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import api from "@/services/api";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    new_password: "",
    new_password_confirm: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.new_password || !formData.new_password_confirm) {
      toast.error("Barcha maydonlarni to'ldiring");
      return;
    }

    if (formData.new_password !== formData.new_password_confirm) {
      toast.error("Parollar mos kelmaydi");
      return;
    }

    if (formData.new_password.length < 8) {
      toast.error("Parol kamida 8 ta belgidan iborat bo'lishi kerak");
      return;
    }

    if (!token) {
      toast.error(
        "Token topilmadi. Iltimos, parolni tiklash jarayonini qaytadan boshlang."
      );
      return;
    }

    setIsLoading(true);

    try {
      await api.post("/api/v1/auth/password-reset/confirm/", {
        token,
        new_password: formData.new_password,
        new_password_confirm: formData.new_password_confirm,
      });

      toast.success("Parol muvaffaqiyatli yangilandi!");
      navigate("/login");
    } catch (error) {
      const errorData = error.response?.data;
      if (errorData?.error) {
        toast.error(errorData.error);
      } else {
        toast.error(
          "Xatolik yuz berdi. Token yaroqsiz yoki muddati o'tgan bo'lishi mumkin."
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-blue-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              Token topilmadi
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Parolni tiklash uchun yaroqli token kerak. Iltimos, jarayonni
              qaytadan boshlang.
            </p>
            <Link
              to="/forgot-password"
              className="mt-4 inline-block btn-primary"
            >
              Parolni tiklash
            </Link>
          </div>
        </div>
      </div>
    );
  }

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
            Yangi parol o'rnatish
          </h2>
          <p className="mt-2 text-center text-sm text-gray-500">
            Yangi parolingizni kiriting
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="new_password"
                className="block text-sm font-medium text-gray-700"
              >
                Yangi parol
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LockClosedIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="new_password"
                  name="new_password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.new_password}
                  onChange={handleChange}
                  className="input-field pl-10 pr-12"
                  placeholder="Kamida 8 ta belgi"
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
                </button>
              </div>
            </div>

            <div>
              <label
                htmlFor="new_password_confirm"
                className="block text-sm font-medium text-gray-700"
              >
                Parolni tasdiqlang
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LockClosedIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="new_password_confirm"
                  name="new_password_confirm"
                  type={showPasswordConfirm ? "text" : "password"}
                  required
                  value={formData.new_password_confirm}
                  onChange={handleChange}
                  className="input-field pl-10 pr-12"
                  placeholder="Parolni qayta kiriting"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-primary-600 transition-colors duration-200"
                >
                  {showPasswordConfirm ? (
                    <EyeSlashIcon className="h-5 w-5" aria-hidden="true" />
                  ) : (
                    <EyeIcon className="h-5 w-5" aria-hidden="true" />
                  )}
                </button>
              </div>
            </div>

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
                  Saqlanmoqda...
                </span>
              ) : (
                "Parolni yangilash"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              ← Tizimga kirishga qaytish
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
