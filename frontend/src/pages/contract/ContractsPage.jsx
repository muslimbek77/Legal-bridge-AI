import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import {
  PlusIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  TrashIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { format } from "date-fns";
import toast from "react-hot-toast";
import LoadingSpinner from "../../components/LoadingSpinner";
import ContractStatusBadge from "../../components/ContractStatusBadge";
import Modal from "../../components/Modal";
import contractsService from "../../services/contracts";
import { CONTRACT_TYPES, STATUS_OPTIONS } from "./contracts.constants";
import useSelection from "../../hooks/useSelection";
import { getRiskScoreStyles } from "@/const/const";

export default function ContractsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);

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

  const contractsList = data?.results || [];
  const hasContracts = contractsList.length > 0;

  const selection = useSelection(contractsList);

  const deleteMutation = useMutation({
    mutationFn: (ids) =>
      Promise.all(ids.map((id) => contractsService.deleteContract(id))),
    onSuccess: () => {
      setDeleteModalOpen(false);
      selection.clear();

      toast.success("Shartnoma o'chirildi");

      queryClient.invalidateQueries({
        queryKey: ["contracts"],
      });
    },
    onError: () => {
      toast.error("Xatolik yuz berdi");
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: contractsService.analyzeContract,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["contracts"],
      });
      toast.success("Tahlil boshlandi");
    },
    onError: () => {
      toast.error("Tahlil boshlashda xatolik");
    },
  });

  const handleDelete = (contract) => {
    setSelectedContract(contract);
    setDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    const ids = selection.selectedIds.length
      ? selection.selectedIds
      : [selectedContract.id];

    deleteMutation.mutate(ids);
  };

  const handleAnalyze = (contractId) => {
    analyzeMutation.mutate(contractId);
  };

  return (
    <div
      className="space-y-6 min-h-screen
                 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))]
                  via-slate-50 to-white"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between
                   px-4 py-3 rounded-xl
                   bg-white/40 backdrop-blur-xl
                   border border-white/40
                   shadow-sm"
      >
        <div>
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Shartnomalar
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Barcha shartnomalarni boshqarish va tahlil qilish
          </p>
        </div>

        <Link
          to="/contracts/upload"
          className="inline-flex items-center px-4 py-2 rounded-lg
                     bg-indigo-600/90 text-white
                     backdrop-blur-md
                     shadow-md hover:shadow-lg
                     transition"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Yangi shartnoma
        </Link>
      </div>

      {/* Filters */}
      <div
        className="p-4 rounded-2xl
                   bg-white/40 backdrop-blur-xl
                   border border-white/40
                   shadow-md"
      >
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Shartnoma qidirish..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg px-3 py-2
                         bg-white/50 backdrop-blur-md
                         border border-white/40
                         focus:outline-none focus:ring-2 focus:ring-indigo-400/40 pl-10"
            />
          </div>

          {/* Type filter */}
          <div className="sm:w-48">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full rounded-lg px-3 py-2
                         bg-white/50 backdrop-blur-md
                         border border-white/40
                         focus:outline-none focus:ring-2 focus:ring-indigo-400/40"
            >
              {CONTRACT_TYPES.map((type) => (
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
              className="w-full rounded-lg px-3 py-2
                         bg-white/50 backdrop-blur-md
                         border border-white/40
                         focus:outline-none focus:ring-2 focus:ring-indigo-400/40"
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div
        className="relative overflow-hidden rounded-3xl
                   bg-white/35 backdrop-blur-2xl
                   border border-white/40
                   shadow-2xl shadow-indigo-200/40"
      >
        {selection.selectedIds.length > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-b bg-white/50 backdrop-blur-xl border-white/30 rounded-t-3xl">
            <span className="text-sm text-gray-700">
              {selection.selectedIds.length} ta shartnoma tanlandi
            </span>
            <button
              onClick={() => setDeleteModalOpen(true)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg
                         bg-red-500/80 text-white shadow-md
                         hover:bg-red-600/90 transition"
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
              <thead className="bg-white/50 backdrop-blur-xl border-b border-white/30">
                <tr>
                  <th className="px-4 text-left py-3">
                    <input
                      type="checkbox"
                      checked={
                        selection.selectedIds.length === contractsList.length &&
                        contractsList.length > 0
                      }
                      onChange={selection.selectAll}
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
              <tbody className="bg-white/40 backdrop-blur-xl divide-y divide-white/20">
                {contractsList.map((contract) => (
                  <tr
                    key={contract.id}
                    className={`
    group cursor-pointer transition-all duration-200
    hover:bg-indigo-50/90
  ${selection.isSelected(contract.id) ? "bg-indigo-100/80" : ""}
  `}
                    onClick={() => navigate(`/contracts/${contract.id}`)}
                  >
                    <td
                      className="px-4 py-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={selection.isSelected(contract.id)}
                        onChange={() => selection.toggle(contract.id)}
                        className="accent-indigo-600 cursor-pointer"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <DocumentTextIcon className="h-8 w-8 text-indigo-500/60 drop-shadow-sm" />
                        <div className="ml-4">
                          <div className="text-sm font-semibold text-gray-900 group-hover:text-indigo-700 transition">
                            {contract.title}
                          </div>
                          <div className="text-sm text-gray-500">
                            {
                              CONTRACT_TYPES.find(
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
                      <div className="inline-flex items-center">
                        <ContractStatusBadge status={contract.status} />
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {contract.risk_score !== null ? (
                        <span
                          className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full
                                      text-sm font-semibold backdrop-blur-md
                                      border shadow-md hover:bg-emerald-300 hover:text-white transition-all duration-200 
                                      ${getRiskScoreStyles(
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
                            className="p-2 rounded-full
                                       bg-white/40 backdrop-blur-md
                                       border border-white/40
                                       shadow-sm
                                       hover:bg-white/60 transition"
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
                          className="p-2 rounded-full cursor-pointer
             bg-red-500/10 text-red-600
             border border-transparent
             group-hover:border-red-300/60
             group-hover:bg-red-500/20
             group-hover:scale-105
             transition-all"
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
        <div className="bg-white/60 backdrop-blur-2xl border border-white/40 p-0 sm:p-0 rounded-xl">
          <p className="text-sm text-gray-500 p-6 pb-0">
            {selection.selectedIds.length > 1
              ? `${selection.selectedIds.length} ta shartnomani o‘chirmoqchimisiz? Bu amalni qaytarib bo‘lmaydi.`
              : `Haqiqatan ham "${selectedContract?.title}" shartnomani o‘chirmoqchimisiz? Bu amalni qaytarib bo‘lmaydi.`}
          </p>
          <div className="mt-6 flex justify-end gap-3 p-6 pt-2">
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
            >
              O'chirish
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
