import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeftIcon, ArrowUpTrayIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import FileUpload from "../components/FileUpload";
import contractsService from "../services/contracts";

const contractTypes = [
  { value: "service", label: "Xizmat ko'rsatish shartnomasi" },
  { value: "supply", label: "Yetkazib berish shartnomasi" },
  { value: "lease", label: "Ijara shartnomasi" },
  { value: "employment", label: "Mehnat shartnomasi" },
  { value: "loan", label: "Kredit shartnomasi" },
  { value: "partnership", label: "Hamkorlik shartnomasi" },
  { value: "nda", label: "Maxfiylik shartnomasi (NDA)" },
  { value: "other", label: "Boshqa" },
];

const languages = [
  { value: "uz_latin", label: "O'zbek (lotin)" },
  { value: "uz_cyrillic", label: "Ўзбек (кирилл)" },
  { value: "ru", label: "Русский" },
];

export default function ContractUploadPage() {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [formData, setFormData] = useState({
    title: "",
    contract_type: "service",
    language: "uz_latin",
    counterparty_name: "",
    counterparty_inn: "",
    contract_number: "",
    description: "",
    auto_analyze: true,
  });

  const uploadMutation = useMutation({
    mutationFn: (data) => contractsService.uploadContract(data),
    onSuccess: (response) => {
      toast.success("Shartnoma muvaffaqiyatli yuklandi!");
      if (formData.auto_analyze) {
        // toast.success("Tahlil boshlandi");
      }
      navigate(`/contracts/${response.id}`);
    },
    onError: (error) => {
      toast.error(
        error.response?.data?.detail || "Yuklashda xatolik yuz berdi"
      );
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();

    if (files.length === 0) {
      toast.error("Fayl tanlang");
      return;
    }

    if (!formData.title) {
      toast.error("Shartnoma nomini kiriting");
      return;
    }

    const data = new FormData();
    data.append("original_file", files[0]);
    data.append("title", formData.title);
    data.append("contract_type", formData.contract_type);
    if (formData.description) {
      data.append("notes", formData.description);
    }

    uploadMutation.mutate(data);
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Orqaga
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          Yangi shartnoma yuklash
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Shartnomani yuklang va avtomatik tahlil qilish uchun ma'lumotlarni
          to'ldiring
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Upload */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Fayl yuklash
          </h3>
          <FileUpload files={files} onFilesChange={setFiles} maxFiles={1} />
        </div>

        {/* Contract Details */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Shartnoma ma'lumotlari
          </h3>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {/* Title */}
            <div className="sm:col-span-2">
              <label
                htmlFor="title"
                className="block text-sm font-medium text-gray-700"
              >
                Shartnoma nomi *
              </label>
              <input
                type="text"
                name="title"
                id="title"
                value={formData.title}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="Masalan: IT xizmatlari shartnomasi"
                required
              />
            </div>

            {/* Contract Type */}
            <div>
              <label
                htmlFor="contract_type"
                className="block text-sm font-medium text-gray-700"
              >
                Shartnoma turi *
              </label>
              <select
                name="contract_type"
                id="contract_type"
                value={formData.contract_type}
                onChange={handleChange}
                className="mt-1 input-field"
                required
              >
                {contractTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Language */}
            <div>
              <label
                htmlFor="language"
                className="block text-sm font-medium text-gray-700"
              >
                Hujjat tili *
              </label>
              <select
                name="language"
                id="language"
                value={formData.language}
                onChange={handleChange}
                className="mt-1 input-field"
                required
              >
                {languages.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Contract Number */}
            <div>
              <label
                htmlFor="contract_number"
                className="block text-sm font-medium text-gray-700"
              >
                Shartnoma raqami
              </label>
              <input
                type="text"
                name="contract_number"
                id="contract_number"
                value={formData.contract_number}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="Masalan: 2024/001"
              />
            </div>

            {/* Counterparty Name */}
            <div>
              <label
                htmlFor="counterparty_name"
                className="block text-sm font-medium text-gray-700"
              >
                Kontragent nomi
              </label>
              <input
                type="text"
                name="counterparty_name"
                id="counterparty_name"
                value={formData.counterparty_name}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="Kompaniya yoki shaxs nomi"
              />
            </div>

            {/* Counterparty INN */}
            <div>
              <label
                htmlFor="counterparty_inn"
                className="block text-sm font-medium text-gray-700"
              >
                Kontragent INN
              </label>
              <input
                type="text"
                name="counterparty_inn"
                id="counterparty_inn"
                value={formData.counterparty_inn}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="9 raqamli INN"
                maxLength={9}
              />
            </div>

            {/* Description */}
            <div className="sm:col-span-2">
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700"
              >
                Qo'shimcha izoh
              </label>
              <textarea
                name="description"
                id="description"
                rows={3}
                value={formData.description}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="Shartnoma haqida qo'shimcha ma'lumotlar"
              />
            </div>

            {/* Auto Analyze */}
            <div className="sm:col-span-2">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="auto_analyze"
                  id="auto_analyze"
                  checked={formData.auto_analyze}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="auto_analyze"
                  className="ml-2 block text-sm text-gray-900"
                >
                  Avtomatik tahlil qilish
                </label>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Shartnoma yuklanganidan so'ng darhol tahlil boshlash
              </p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn-secondary"
          >
            Bekor qilish
          </button>
          <button
            type="submit"
            disabled={
              uploadMutation.isPending ||
              files.length === 0 ||
              !formData.title.trim()
            }
            className="btn-primary"
          >
            {uploadMutation.isPending ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Yuklanmoqda...
              </span>
            ) : (
              <span className="flex items-center">
                <ArrowUpTrayIcon className="h-5 w-5 mr-2" />
                Yuklash
              </span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
