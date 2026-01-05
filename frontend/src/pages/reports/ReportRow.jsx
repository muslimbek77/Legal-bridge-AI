// src/pages/reports/ReportRow.jsx
import { format } from "date-fns";
import { ArrowDownTrayIcon, TrashIcon } from "@heroicons/react/24/outline";
import { formatFileSize } from "./reports.utils";
import { getRiskScoreStyles } from "@/const/const";

export default function ReportRow({
  report,
  onDownload,
  onDelete,
  isSelected,
  onToggle,
}) {
  const RISK_BADGE_BASE =
    "inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold backdrop-blur-md border shadow-md transition-all duration-200";

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggle}
          className="accent-indigo-600 cursor-pointer"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900">
          {report.contract_title}
        </div>
      </td>

      <td className="px-6 py-4 whitespace-nowrap">
        <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800 uppercase">
          {report.format_display}
        </span>
      </td>

      <td className="px-6 py-4 whitespace-nowrap">
        <span
          className={`${RISK_BADGE_BASE} ${getRiskScoreStyles(
            report.risk_score
          )}`}
        >
          {report.risk_score}
        </span>
      </td>

      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {formatFileSize(report.file_size)}
      </td>

      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {format(new Date(report.created_at), "dd.MM.yyyy HH:mm")}
      </td>

      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={() => onDownload(report)}
            className="text-indigo-600 hover:text-indigo-900"
            title="Yuklab olish"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
          </button>

          <button
            onClick={() => onDelete(report)}
            className="text-red-600 hover:text-red-900"
            title="O'chirish"
          >
            <TrashIcon className="h-5 w-5" />
          </button>
        </div>
      </td>
    </tr>
  );
}
