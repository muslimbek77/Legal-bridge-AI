import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";
import { format } from "date-fns";
import toast from "react-hot-toast";
import LoadingSpinner from "../../components/LoadingSpinner";
import Modal from "../../components/Modal";
import reportsService from "../../services/reports";

import { useEffect } from "react";
import { DeleteOutlined, DownloadOutlined } from "@ant-design/icons";
import useDebounce from "../../hooks/useDebounce";
import { getRiskScoreStyles } from "@/const/const";
import { formatFileSize } from "./reports.utils";
import ReportRow from "./ReportRow";
import ReportsFilters from "./ReportsFilters";
import useSelection from "@/hooks/useSelection";

export default function ReportsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [formatFilter, setFormatFilter] = useState("");
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [emailAddress, setEmailAddress] = useState("");

  const debouncedSearch = useDebounce(searchTerm, 500);

  const queryClient = useQueryClient();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["reports", debouncedSearch, formatFilter],
    queryFn: () =>
      reportsService.getReports({
        search: debouncedSearch,
        format: formatFilter,
      }),
    keepPreviousData: true,
  });

  const deleteMutation = useMutation({
    mutationFn: (ids) =>
      Promise.all(ids.map((id) => reportsService.deleteReport(id))),
    onSuccess: () => {
      queryClient.invalidateQueries(["reports"]);
      toast.success("Hisobot o'chirildi");
      setDeleteModalOpen(false);
      selection.clear();
    },
    onError: () => {
      toast.error("Xatolik yuz berdi");
    },
  });

  const sendEmailMutation = useMutation({
    mutationFn: ({ id, email }) => reportsService.sendByEmail(id, email),
    onSuccess: () => {
      toast.success("Hisobot yuborildi");
      setEmailModalOpen(false);
      setEmailAddress("");
    },
    onError: () => {
      toast.error("Yuborishda xatolik");
    },
  });

  // Haqiqiy ma'lumotlarni ishlatish
  const reportsList = data?.results || [];
  const hasReports = reportsList.length > 0;
  const selection = useSelection(reportsList);

  const handleDownload = async (report) => {
    try {
      const blob = await reportsService.downloadReport(report.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${report.contract_title}.${report.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success("Hisobot yuklab olindi");
    } catch {
      toast.error("Yuklab olishda xatolik");
    }
  };

  const handleDelete = (report) => {
    setSelectedReport(report);
    setDeleteModalOpen(true);
  };

  const handleEmail = (report) => {
    setSelectedReport(report);
    setEmailModalOpen(true);
  };

  const confirmDelete = () => {
    const ids = selection.selectedIds.length
      ? selection.selectedIds
      : selectedReport
      ? [selectedReport.id]
      : [];

    if (!ids.length) return;

    deleteMutation.mutate(ids);
  };

  const confirmSendEmail = () => {
    if (selectedReport && emailAddress) {
      sendEmailMutation.mutate({ id: selectedReport.id, email: emailAddress });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Hisobotlar</h1>
        <p className="mt-1 text-sm text-gray-500">
          Yaratilgan tahlil hisobotlari
        </p>
      </div>

      {/* Filters */}
      <ReportsFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        formatFilter={formatFilter}
        onFormatChange={setFormatFilter}
      />

      {selection.selectedIds.length > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-b bg-white">
          <span className="text-sm text-gray-700">
            {selection.selectedIds.length} ta hisobot tanlandi
          </span>
          <button
            onClick={() => setDeleteModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-red-600 text-white hover:bg-red-700 transition"
          >
            Tanlanganlarni o‘chirish
          </button>
        </div>
      )}
      {/* Reports Table */}
      <div className="card overflow-hidden">
        {isFetching && (
          <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-10">
            <LoadingSpinner size="sm" />
          </div>
        )}
        {!hasReports ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <DocumentArrowDownIcon className="h-12 w-12 mb-4" />
            <p className="text-lg font-medium">Hisobotlar topilmadi</p>
            <p className="text-sm">
              Shartnomalarni tahlil qilib hisobot yarating
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 flex items-start">
                    <input
                      type="checkbox"
                      checked={
                        selection.selectedIds.length === reportsList.length &&
                        reportsList.length > 0
                      }
                      onChange={selection.selectAll}
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Shartnoma
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Format
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Ball
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Hajmi
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
                {reportsList.map((report) => (
                  <ReportRow
                    key={report.id}
                    report={report}
                    onDownload={handleDownload}
                    onDelete={handleDelete}
                    isSelected={selection.isSelected(report.id)}
                    onToggle={() => selection.toggle(report.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Hisobotni o'chirish"
      >
        <p className="text-sm text-gray-500">
          {selection.selectedIds.length > 1
            ? `${selection.selectedIds.length} ta hisobotni o‘chirmoqchimisiz? Bu amalni qaytarib bo‘lmaydi.`
            : "Haqiqatan ham bu hisobotni o'chirmoqchimisiz?"}
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

      {/* Email Modal */}
      <Modal
        isOpen={emailModalOpen}
        onClose={() => setEmailModalOpen(false)}
        title="Hisobotni yuborish"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            Hisobotni qaysi email manziliga yubormoqchisiz?
          </p>
          <input
            type="email"
            value={emailAddress}
            onChange={(e) => setEmailAddress(e.target.value)}
            placeholder="email@example.com"
            className="input-field"
          />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setEmailModalOpen(false)}
          >
            Bekor qilish
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={confirmSendEmail}
            disabled={sendEmailMutation.isPending || !emailAddress}
          >
            {sendEmailMutation.isPending ? "Yuborilmoqda..." : "Yuborish"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
