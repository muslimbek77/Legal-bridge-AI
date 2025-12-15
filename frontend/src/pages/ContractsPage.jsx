import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  DocumentTextIcon,
  TrashIcon,
  EyeIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { format } from "date-fns";
import toast from "react-hot-toast";
import LoadingSpinner from "../components/LoadingSpinner";
import ContractStatusBadge from "../components/ContractStatusBadge";
import Modal from "../components/Modal";
import contractsService from "../services/contracts";

export default function ContractsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);

  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["contracts", searchTerm, statusFilter, typeFilter],
    queryFn: () =>
      contractsService.getContracts({
        search: searchTerm,
        status: statusFilter,
        contract_type: typeFilter,
      }),
  });
  // console.log(data);

  const deleteMutation = useMutation({
    mutationFn: (ids) =>
      Promise.all(ids.map((id) => contractsService.deleteContract(id))),
    onSuccess: () => {
      queryClient.invalidateQueries(["contracts"]);
      toast.success("Shartnoma o'chirildi");
      setDeleteModalOpen(false);
    },
    onError: () => {
      toast.error("Xatolik yuz berdi");
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: contractsService.analyzeContract,
    onSuccess: () => {
      queryClient.invalidateQueries(["contracts"]);
      toast.success("Tahlil boshlandi");
    },
    onError: () => {
      toast.error("Tahlil boshlashda xatolik");
    },
  });

  // Haqiqiy ma'lumotlarni ishlatish
  const contractsList = data?.results || [];
  const hasContracts = contractsList.length > 0;

  const contractTypes = [
    { value: "", label: "Barcha turlar" },
    { value: "service", label: "Xizmat ko'rsatish" },
    { value: "supply", label: "Yetkazib berish" },
    { value: "lease", label: "Ijara" },
    { value: "employment", label: "Mehnat" },
    { value: "loan", label: "Kredit" },
    { value: "other", label: "Boshqa" },
  ];

  const statusOptions = [
    { value: "", label: "Barcha statuslar" },
    { value: "draft", label: "Qoralama" },
    { value: "pending", label: "Kutilmoqda" },
    { value: "processing", label: "Tahlil qilinmoqda" },
    { value: "analyzed", label: "Tahlil qilindi" },
    { value: "approved", label: "Tasdiqlandi" },
    { value: "rejected", label: "Rad etildi" },
  ];

  const handleDelete = (contract) => {
    setSelectedContract(contract);
    setDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    const ids = selectedIds.length ? selectedIds : [selectedContract.id];
    deleteMutation.mutate(ids);
    setSelectedIds([]);
  };

  const handleAnalyze = (contractId) => {
    analyzeMutation.mutate(contractId);
  };

  const getRiskScoreClass = (score) => {
    if (score === null) return "";
    if (score < 25) return "bg-green-100 text-green-800";
    if (score < 50) return "bg-yellow-100 text-yellow-800";
    if (score < 75) return "bg-orange-100 text-orange-800";
    return "bg-red-100 text-red-800";
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === contractsList.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(contractsList.map((c) => c.id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Shartnomalar</h1>
          <p className="mt-1 text-sm text-gray-500">
            Barcha shartnomalarni boshqarish va tahlil qilish
          </p>
        </div>

        <Link to="/contracts/upload" className="btn-primary">
          <PlusIcon className="h-5 w-5 mr-2" />
          Yangi shartnoma
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Shartnoma qidirish..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>

          {/* Type filter */}
          <div className="sm:w-48">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="input-field"
            >
              {contractTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <div className="sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              {statusOptions.map((status) => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {selectedIds.length > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-b bg-red-50">
            <span className="text-sm text-gray-700">
              {selectedIds.length} ta shartnoma tanlandi
            </span>
            <button
              onClick={() => setDeleteModalOpen(true)}
              className="btn-danger"
            >
              Tanlanganlarni o‘chirish
            </button>
          </div>
        )}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : !hasContracts ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <DocumentTextIcon className="h-16 w-16 mb-4" />
            <p className="text-lg font-medium text-gray-600 mb-2">
              Shartnomalar topilmadi
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Birinchi shartnomangizni yuklang va tahlil qiling
            </p>
            <Link to="/contracts/upload" className="btn-primary">
              <PlusIcon className="h-5 w-5 mr-2" />
              Shartnoma yuklash
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 text-left py-3">
                    <input
                      type="checkbox"
                      checked={
                        selectedIds.length === contractsList.length &&
                        contractsList.length > 0
                      }
                      onChange={selectAll}
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Shartnoma
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Turi
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Ball
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sana
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amallar
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {contractsList.map((contract) => (
                  <tr
                    key={contract.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/contracts/${contract.id}`)}
                  >
                    <td
                      className="px-4 py-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(contract.id)}
                        onChange={() => toggleSelect(contract.id)}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {contract.title}
                          </div>
                          <div className="text-sm text-gray-500">
                            {
                              contractTypes.find(
                                (t) => t.value === contract.contract_type
                              )?.label
                            }
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {contract.contract_type_display}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <ContractStatusBadge status={contract.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {contract.risk_score !== null ? (
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskScoreClass(
                            contract.risk_score
                          )}`}
                        >
                          {contract.risk_score}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(contract.created_at), "dd.MM.yyyy")}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        {(contract.status === "pending" ||
                          contract.status === "draft") && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAnalyze(contract.id);
                            }}
                            className="text-green-600 hover:text-green-900"
                            title="Tahlil qilish"
                            disabled={analyzeMutation.isPending}
                          >
                            <ArrowPathIcon className="h-5 w-5" />
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(contract);
                          }}
                          className="text-red-600 hover:text-red-900"
                          title="O'chirish"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {isFetching && !isLoading && (
          <div className="absolute inset-0 bg-white/50 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        )}
      </div>

      {/* Delete Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Shartnomani o'chirish"
      >
        <p className="text-sm text-gray-500">
          {selectedIds.length > 1
            ? `${selectedIds.length} ta shartnomani o‘chirmoqchimisiz? Bu amalni qaytarib bo‘lmaydi.`
            : `Haqiqatan ham "${selectedContract?.title}" shartnomani o‘chirmoqchimisiz? Bu amalni qaytarib bo‘lmaydi.`}
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setDeleteModalOpen(false)}
          >
            Bekor qilish
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={confirmDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "O'chirilmoqda..." : "O'chirish"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
