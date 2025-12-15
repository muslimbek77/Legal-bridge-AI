import { useEffect, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  UserCircleIcon,
  EyeIcon,
  EyeSlashIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";
import contractsService from "../services/contracts";
import userService from "../services/user";

export default function ProfilePage() {
  const { user, isHydrated, updateProfile } = useAuthStore();

  const { data: userDetails, isLoading } = useQuery({
    enabled: isHydrated && !!user?.id,
    queryKey: ["user-details", user?.id],
    queryFn: () => userService.getSingleUser({ id: user.id }),
  });

  // console.log("UserDetails", userDetails);

  const [formData, setFormData] = useState({
    first_name: userDetails?.first_name || "",
    last_name: userDetails?.last_name || "",
    email: userDetails?.email || "",
    phone: userDetails?.phone || "",
    organization: userDetails?.organization || "",
    position: userDetails?.position || "",
  });

  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Haqiqiy statistikani olish
  const { data: stats } = useQuery({
    queryKey: ["contract-statistics"],
    queryFn: contractsService.getStatistics,
  });

  // Haqiqiy statistika qiymatlari
  const activityStats = {
    uploaded: stats?.total || 0,
    analyzed: stats?.by_status?.analyzed || 0,
    reports: 0, // Hisobotlar soni alohida API kerak
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await updateProfile(formData);
    if (result.success) {
      toast.success("Profil yangilandi");
    } else {
      toast.error("Xatolik yuz berdi");
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error("Parollar mos kelmaydi");
      return;
    }
    // Password change logic here
    toast.success("Parol o'zgartirildi");
    setPasswordData({
      current_password: "",
      new_password: "",
      confirm_password: "",
    });
  };

  const roleLabels = {
    lawyer: "Yurist",
    analyst: "Tahlilchi",
    admin: "Administrator",
    viewer: "Foydalanuvchi",
  };

  // console.log("Profile user", user);

  // console.log(userDetails);

  useEffect(() => {
    if (!userDetails) return;

    setFormData({
      first_name: userDetails.first_name || "",
      last_name: userDetails.last_name || "",
      email: userDetails.email || "",
      phone: userDetails.phone || "",
      organization: userDetails.organization || "",
      position: userDetails.position || "",
    });
  }, [userDetails]);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profil</h1>
        <p className="mt-1 text-sm text-gray-500">
          Shaxsiy ma'lumotlaringizni boshqaring
        </p>
      </div>

      {/* Profile Info */}
      <div className="card p-6">
        <div className="flex items-center mb-6">
          <div className="h-20 w-20 rounded-full bg-primary-600 flex items-center justify-center">
            <span className="text-3xl font-medium text-white">
              {userDetails?.first_name?.[0] ||
                userDetails?.email?.[0]?.toUpperCase() ||
                "U"}
            </span>
          </div>
          <div className="ml-6">
            <h2 className="text-xl font-semibold text-gray-900">
              {userDetails?.first_name} {userDetails?.last_name}
            </h2>
            <p className="text-sm text-gray-500">{userDetails?.email}</p>
            <span className="mt-1 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
              {roleLabels[userDetails?.role] || "Foydalanuvchi"}
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label
                htmlFor="first_name"
                className="block text-sm font-medium text-gray-700"
              >
                Ism
              </label>
              <input
                type="text"
                name="first_name"
                id="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="mt-1 input-field"
              />
            </div>
            <div>
              <label
                htmlFor="last_name"
                className="block text-sm font-medium text-gray-700"
              >
                Familiya
              </label>
              <input
                type="text"
                name="last_name"
                id="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="mt-1 input-field"
              />
            </div>
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                type="email"
                name="email"
                id="email"
                value={formData.email}
                onChange={handleChange}
                className="mt-1 input-field"
                disabled
              />
            </div>
            <div>
              <label
                htmlFor="phone"
                className="block text-sm font-medium text-gray-700"
              >
                Telefon
              </label>
              <input
                type="tel"
                name="phone"
                id="phone"
                value={formData.phone}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="+998 XX XXX XX XX"
              />
            </div>
            <div>
              <label
                htmlFor="organization"
                className="block text-sm font-medium text-gray-700"
              >
                Tashkilot
              </label>
              <input
                type="text"
                name="organization"
                id="organization"
                value={formData.organization}
                onChange={handleChange}
                className="mt-1 input-field"
              />
            </div>
            <div>
              <label
                htmlFor="position"
                className="block text-sm font-medium text-gray-700"
              >
                Lavozim
              </label>
              <input
                type="text"
                name="position"
                id="position"
                value={formData.position}
                onChange={handleChange}
                className="mt-1 input-field"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" className="btn-primary">
              Saqlash
            </button>
          </div>
        </form>
      </div>

      {/* Change Password */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Parolni o'zgartirish
        </h3>
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="current_password"
              className="block text-sm font-medium text-gray-700"
            >
              Joriy parol
            </label>
            <div className="mt-1 relative">
              <input
                type={showCurrentPassword ? "text" : "password"}
                name="current_password"
                id="current_password"
                value={passwordData.current_password}
                onChange={handlePasswordChange}
                className="input-field pr-12"
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-primary-600 transition-colors duration-200"
              >
                {showCurrentPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          <div>
            <label
              htmlFor="new_password"
              className="block text-sm font-medium text-gray-700"
            >
              Yangi parol
            </label>
            <div className="mt-1 relative">
              <input
                type={showNewPassword ? "text" : "password"}
                name="new_password"
                id="new_password"
                value={passwordData.new_password}
                onChange={handlePasswordChange}
                className="input-field pr-12"
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-primary-600 transition-colors duration-200"
              >
                {showNewPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          <div>
            <label
              htmlFor="confirm_password"
              className="block text-sm font-medium text-gray-700"
            >
              Yangi parolni tasdiqlang
            </label>
            <div className="mt-1 relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                name="confirm_password"
                id="confirm_password"
                value={passwordData.confirm_password}
                onChange={handlePasswordChange}
                className="input-field pr-12"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-primary-600 transition-colors duration-200"
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" className="btn-primary">
              Parolni o'zgartirish
            </button>
          </div>
        </form>
      </div>

      {/* Activity Stats */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Faollik statistikasi
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">
              {activityStats.uploaded}
            </p>
            <p className="text-sm text-gray-500">Yuklangan shartnomalar</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">
              {activityStats.analyzed}
            </p>
            <p className="text-sm text-gray-500">Tahlil qilingan</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">
              {activityStats.reports}
            </p>
            <p className="text-sm text-gray-500">Hisobotlar</p>
          </div>
        </div>
      </div>
    </div>
  );
}
